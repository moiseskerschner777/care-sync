import uuid
from datetime import datetime, timedelta
import random

from simulators.covenant import simulate_covenant


def approved_response(payload: dict) -> dict:
    return {
        "authorization_id": str(uuid.uuid4()),
        "status": "approved",
        "covenant_id": payload.get("covenant_id", ""),
        "patient_id": payload.get("patient_id", ""),
        "exam_code": payload.get("exam_code", ""),
        "valid_until": (datetime.utcnow() + timedelta(days=30)).isoformat() + "Z",
        "protocol": f"VITA-{random.randint(10000, 99999)}",
        "message": "Pre-authorization approved.",
    }


def simulate(payload: dict) -> tuple[int, dict]:
    covenant_id = payload.get("covenant_id", "")
    trigger_result = simulate_covenant(covenant_id)
    if trigger_result is not None:
        return trigger_result
    return (201, approved_response(payload))
