from simulators.error_response import operation_outcome


def check_partial(payload: dict):
    extensions = payload.get("extension", [])
    batch_id = None
    for ext in extensions:
        if ext.get("url") == "batch_id":
            batch_id = ext.get("valueString", "")
            break

    if not batch_id:
        return None

    if batch_id == "ERR-PARTIAL":
        body = {
            "resourceType": "OperationOutcome",
            "issue": [{"severity": "information", "code": "informational",
                       "diagnostics": "Partial success"}],
            "accepted": [
                {"item": 1, "status": "accepted"},
                {"item": 2, "status": "accepted"},
            ],
            "rejected": [
                {"item": 3, "status": "rejected",
                 "reason": "exam not available in RefLab catalog"},
            ],
        }
        return (207, body)

    if batch_id == "ERR-WARNING":
        body = {
            "resourceType": "DiagnosticReport",
            "status": "final",
            "warnings": ["sample volume low"],
        }
        return (200, body)

    if batch_id == "ERR-BODY-MISMATCH":
        body = {
            "resourceType": "DiagnosticReport",
            "status": "final",
            "error": "internal processing error",
        }
        return (200, body)

    if batch_id == "ERR-EMPTY":
        return (200, {})

    if batch_id == "ERR-PARTIAL-CANCEL":
        body = {
            "resourceType": "OperationOutcome",
            "issue": [{"severity": "information", "code": "informational",
                       "diagnostics": "Partial cancellation"}],
            "cancelled": [
                {"item": 1, "status": "cancelled"},
            ],
            "failed": [
                {"item": 2, "status": "failed",
                 "reason": "sample already in analyzer"},
            ],
        }
        return (207, body)

    return None
