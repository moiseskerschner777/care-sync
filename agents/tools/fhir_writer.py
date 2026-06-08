import base64
import datetime
import json
import logging
import uuid

import httpx

from config import settings
from database import SessionLocal
from memory.error_dedup import compute_hashes
from models.error_report import ErrorReport

logger = logging.getLogger(__name__)


def _auth_header() -> str:
    credentials = f"{settings.iris_username}:{settings.iris_password}"
    encoded = base64.b64encode(credentials.encode()).decode()
    return f"Basic {encoded}"


def _post_resource(resource_type: str, resource: dict) -> str | None:
    url = f"{settings.fhir_base_url}/{resource_type}"
    try:
        with httpx.Client(timeout=10) as client:
            resp = client.post(
                url,
                json=resource,
                headers={
                    "Content-Type": "application/fhir+json",
                    "Authorization": _auth_header(),
                },
            )
        if 200 <= resp.status_code < 300:
            returned_id = resource.get("id")
            if resp.headers.get("Location"):
                location = resp.headers["Location"]
                parts = location.rstrip("/").split("/")
                try:
                    history_idx = parts.index("_history")
                    returned_id = parts[history_idx - 1] if history_idx > 0 else returned_id
                except ValueError:
                    returned_id = parts[-1] if parts else returned_id
            try:
                body = resp.json()
                if body and body.get("id"):
                    returned_id = body["id"]
            except (json.JSONDecodeError, AttributeError):
                pass
            logger.info("FHIR %s created id=%s", resource_type, returned_id)
            return returned_id
        else:
            logger.warning("FHIR %s POST failed status=%s body=%s", resource_type, resp.status_code, resp.text)
            return None
    except httpx.RequestError as e:
        logger.error("FHIR %s POST error: %s", resource_type, e)
        return None


def write_task(operation: str, system_target: str, response: dict) -> bool:
    resource_id = str(uuid.uuid4())
    now = datetime.datetime.utcnow().isoformat() + "Z"

    task = {
        "resourceType": "Task",
        "id": resource_id,
        "status": "completed",
        "intent": "order",
        "code": {
            "coding": [{
                "system": "http://hl7.org/fhir/CodeSystem/task-code",
                "code": "fulfill"
            }],
            "text": "MedBridge Agent Routing"
        },
        "description": f"Routed {operation} to {system_target}",
        "authoredOn": now,
        "lastModified": now,
        "executionPeriod": {
            "start": now,
            "end": now
        },
        "note": [{
            "text": f"Response: {json.dumps(response, default=str)}"
        }],
        "input": [{
            "type": {"text": "operation"},
            "valueString": operation
        }, {
            "type": {"text": "system_target"},
            "valueString": system_target
        }]
    }
    return _post_resource("Task", task) is not None


def write_error_report(
    operation: str,
    system_target: str,
    diagnosis: dict,
    payload_sent: dict,
    raw_error: dict,
    audit_event_id: str,
) -> bool:
    db = SessionLocal()
    try:
        ph, eh = compute_hashes(payload_sent, raw_error)
        report = ErrorReport(
            id=str(uuid.uuid4()),
            created_at=datetime.datetime.utcnow(),
            system_target=system_target,
            operation=operation,
            origin=diagnosis.get("origin", "AMBIGUOUS"),
            confidence=diagnosis.get("confidence", 0),
            evidence=diagnosis.get("evidence", ""),
            suggestion=diagnosis.get("suggestion", ""),
            payload_sent=json.dumps(payload_sent, default=str),
            raw_error=json.dumps(raw_error, default=str),
            audit_event_id=audit_event_id,
            payload_hash=ph,
            raw_error_hash=eh,
        )
        db.add(report)
        db.commit()
        logger.info("error_report saved id=%s audit_event_id=%s", report.id, audit_event_id)
        return True
    except Exception as e:
        logger.error("error_report save failed: %s", e)
        db.rollback()
        return False
    finally:
        db.close()


def write_audit_event(operation: str, system_target: str,
                      diagnosis: dict, payload_sent: dict,
                      raw_error: dict) -> bool:
    resource_id = str(uuid.uuid4())
    now = datetime.datetime.utcnow().isoformat() + "Z"

    origin = diagnosis.get("origin", "AMBIGUOUS")
    confidence = diagnosis.get("confidence", 0)

    outcome_map = {
        "ORIGIN_A": "8",
        "ORIGIN_B": "8",
        "CONTRACT": "4",
        "INFRA": "12",
        "AMBIGUOUS": "4",
    }

    audit = {
        "resourceType": "AuditEvent",
        "id": resource_id,
        "type": {
            "system": "http://terminology.hl7.org/CodeSystem/audit-event-type",
            "code": "110106",
            "display": "Export"
        },
        "action": "E",
        "recorded": now,
        "outcome": outcome_map.get(origin, "4"),
        "outcomeDesc": f"[{origin}] confidence={confidence:.0%} — {system_target}/{operation}",
        "agent": [{
            "who": {
                "identifier": {"value": "MedBridge Agent"}
            },
            "requestor": True,
            "role": [{
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/v3-RoleCode",
                    "code": "AUT",
                    "display": "author"
                }]
            }]
        }],
        "source": {
            "observer": {
                "identifier": {"value": "MedBridge Agent"}
            }
        },
        "entity": [{
            "what": {
                "identifier": {"value": system_target}
            },
            "type": {
                "system": "http://terminology.hl7.org/CodeSystem/audit-entity-type",
                "code": "2",
                "display": "System Object"
            },
            "role": {
                "system": "http://terminology.hl7.org/CodeSystem/object-role",
                "code": "13",
                "display": "Security Resource"
            },
            "detail": [{
                "type": "operation",
                "valueString": operation
            }, {
                "type": "payload_sent",
                "valueString": f"see error_report id={resource_id}"
            }]
        }]
    }

    audit_event_id = _post_resource("AuditEvent", audit)
    if audit_event_id is None:
        return False

    report_ok = write_error_report(
        operation=operation,
        system_target=system_target,
        diagnosis=diagnosis,
        payload_sent=payload_sent,
        raw_error=raw_error,
        audit_event_id=audit_event_id,
    )
    return report_ok
