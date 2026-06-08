import json
import logging

from config import settings

logger = logging.getLogger(__name__)


def resolve_targets(service_request: dict, exam_items: list[dict]) -> list[str]:
    targets = []
    has_external = any(not item.get("can_perform", True) for item in exam_items)
    has_covenant = bool(service_request.get("covenant_id"))

    if has_external:
        targets.append("reflab")
    if has_covenant:
        targets.append("vitacare")

    return targets


def build_reflab_payload(service_request: dict, exam_items: list[dict]) -> dict:
    external_exam = next(
        (item for item in exam_items if not item.get("can_perform", True)),
        exam_items[0] if exam_items else {},
    )
    return {
        "operation": "create_exam",
        "system_target": "reflab",
        "payload": {
            "service_request_id": service_request.get("code", ""),
            "exam_code": external_exam.get("exam_code", ""),
            "patient_id": service_request.get("patient_id", ""),
            "practitioner_id": service_request.get("practitioner_id", ""),
        },
    }


def build_vitacare_payload(service_request: dict) -> dict:
    items = service_request.get("items", [])
    exam_code = items[0]["exam_code"] if items else ""
    return {
        "operation": "validate_coverage",
        "system_target": "vitacare",
        "payload": {
            "service_request_id": service_request.get("code", ""),
            "covenant_id": service_request.get("covenant_id", ""),
            "patient_id": service_request.get("patient_id", ""),
            "exam_code": exam_code,
            "practitioner_id": service_request.get("practitioner_id", ""),
            "cid_code": service_request.get("cid_code", ""),
        },
    }


def trigger_agent(service_request: dict, exam_items: list[dict]):
    import httpx

    targets = resolve_targets(service_request, exam_items)
    if not targets:
        return

    builders = {
        "reflab": lambda: build_reflab_payload(service_request, exam_items),
        "vitacare": lambda: build_vitacare_payload(service_request),
    }

    for target in targets:
        try:
            payload = builders[target]()
            url = f"{settings.agent_url}/agent/invoke"
            logger.info("▶ %s → %s\n%s", "labcore", target, json.dumps(payload, indent=2))
            resp = httpx.post(
                url,
                json=payload,
                timeout=60.0,
            )
            logger.info("◀ %s | %s\n%s", resp.status_code, url, resp.text[:2000])
        except Exception as e:
            logger.error("agent trigger failed target=%s error=%s", target, e)
