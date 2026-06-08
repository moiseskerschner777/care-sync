import uuid
from datetime import datetime, timezone


def extract_exam_code(payload: dict) -> str:
    try:
        return (
            payload["entry"][0]["resource"]["code"]["coding"][0]["code"]
        )
    except (KeyError, IndexError, TypeError):
        pass
    return payload.get("exam_code", "")


def extract_patient_id(payload: dict) -> str:
    try:
        ref = payload["entry"][0]["resource"]["subject"]["reference"]
        if ref.startswith("Patient/"):
            return ref[len("Patient/"):]
        return ref
    except (KeyError, IndexError, TypeError):
        pass
    return payload.get("patient_id", "")


def synthetic_diagnostic_report(payload: dict) -> dict:
    exam_code = extract_exam_code(payload) or "unknown"
    exam_display = exam_code
    patient_id = extract_patient_id(payload) or "unknown"
    order_id = payload.get("id", "unknown")

    return {
        "resourceType": "DiagnosticReport",
        "id": str(uuid.uuid4()),
        "status": "final",
        "code": {
            "coding": [{
                "system": "http://loinc.org",
                "code": exam_code,
                "display": exam_display,
            }]
        },
        "subject": {
            "reference": f"Patient/{patient_id}"
        },
        "basedOn": [{
            "reference": f"ServiceRequest/{order_id}"
        }],
        "issued": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "conclusion": "Result within normal range.",
        "result": [{
            "reference": "Observation/simulated-001"
        }],
    }


def simulate(payload: dict) -> tuple[int, dict]:
    from simulators.identity import check_identity
    from simulators.exam import check_exam
    from simulators.sample import check_sample
    from simulators.timing import check_timing
    from simulators.format import check_format
    from simulators.partial import check_partial

    result = check_identity(payload)
    if result is not None:
        return result

    result = check_exam(payload)
    if result is not None:
        return result

    result = check_sample(payload)
    if result is not None:
        return result

    result = check_timing(payload)
    if result is not None:
        return result

    result = check_format(payload)
    if result is not None:
        return result

    result = check_partial(payload)
    if result is not None:
        return result

    return (201, synthetic_diagnostic_report(payload))
