HTTP_TO_FHIR_CODE = {
    404: "not-found",
    409: "conflict",
    410: "gone",
    422: "value",
    408: "timeout",
}


def operation_outcome(http_code: int, message: str, trigger: str) -> dict:
    fhir_code = HTTP_TO_FHIR_CODE.get(http_code, "processing")
    return {
        "resourceType": "OperationOutcome",
        "issue": [{
            "severity": "error",
            "code": fhir_code,
            "diagnostics": message,
            "details": {
                "text": trigger,
            },
        }],
    }
