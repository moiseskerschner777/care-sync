import copy
import hashlib
import json
import logging

from sqlalchemy.orm import Session

from models.error_report import ErrorReport

logger = logging.getLogger(__name__)

# Fields that differ between requests but carry no diagnostic meaning.
# Stripped from the payload before hashing so the same logical error
# (same exam code, same error response) always produces the same hash
# regardless of which patient / service-request triggered it.
_DYNAMIC_FIELDS = {"service_request_id", "patient_id", "practitioner_id"}


def _normalize_payload(payload: dict) -> dict:
    """
    Return a copy of *payload* with per-request dynamic fields removed.

    Also strips dynamic identifiers from the first FHIR Bundle entry
    (subject, requester, resource id) so that structural/semantic content
    — primarily the exam code — drives the hash.
    """
    p = copy.deepcopy(payload)

    # Remove top-level dynamic keys
    for key in _DYNAMIC_FIELDS:
        p.pop(key, None)

    # Strip dynamic values from the first FHIR Bundle entry if present
    entries = p.get("entry")
    if isinstance(entries, list) and entries:
        resource = entries[0].get("resource", {})
        resource.pop("id", None)
        resource.pop("subject", None)
        resource.pop("requester", None)

    return p


def _hash(data: dict) -> str:
    """SHA-256 of deterministic JSON serialization."""
    canonical = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode()).hexdigest()


def compute_hashes(payload_sent: dict, raw_error: dict) -> tuple[str, str]:
    """
    Compute (payload_hash, raw_error_hash).
    payload_sent is normalized before hashing to strip per-request IDs.
    """
    return _hash(_normalize_payload(payload_sent)), _hash(raw_error)


def find_duplicate_diagnosis(
    db: Session,
    operation: str,
    system_target: str,
    payload_sent: dict,
    raw_error: dict,
) -> dict | None:
    """
    Look up a previous diagnosis for the same logical error:
    (operation, system_target, normalized_payload, raw_error).
    Returns the stored diagnosis dict or None if no match is found.
    """
    ph, eh = compute_hashes(payload_sent, raw_error)

    row = (
        db.query(ErrorReport)
        .filter_by(
            operation=operation,
            system_target=system_target,
            payload_hash=ph,
            raw_error_hash=eh,
        )
        .order_by(ErrorReport.created_at.desc())
        .first()
    )

    if row is None:
        return None

    return {
        "id": row.id,
        "origin": row.origin,
        "confidence": row.confidence,
        "evidence": row.evidence,
        "suggestion": row.suggestion,
    }
