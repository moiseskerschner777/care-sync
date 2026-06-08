def rejected(error_code: str, message: str, covenant_id: str, details: str = "") -> dict:
    return {
        "status": "rejected",
        "error_code": error_code,
        "message": message,
        "covenant_id": covenant_id,
        "details": details,
    }
