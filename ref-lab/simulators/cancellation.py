from simulators.error_response import operation_outcome


def simulate_cancel(cancel_id: str):
    if cancel_id == "ERR-NOT-PROPAGATED":
        return (200, {"resourceType": "OperationOutcome", "propagated": False,
                       "diagnostics": "Cancellation acknowledged but not propagated"})

    if cancel_id == "ERR-PROCESSING":
        return (409, operation_outcome(409, "Sample already in analyzer", cancel_id))

    if cancel_id == "ERR-RESULT-ISSUED":
        return (422, operation_outcome(422, "DiagnosticReport already signed", cancel_id))

    if cancel_id == "ERR-PARTIAL-CANCEL":
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

    return (200, {"status": "cancelled", "id": cancel_id})
