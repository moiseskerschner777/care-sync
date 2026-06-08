import time
from simulators.error_response import operation_outcome

_seen_order_ids: set[str] = set()


def check_timing(payload: dict):
    import time as _time

    order_id = payload.get("id", "")
    if not order_id:
        return None

    if order_id == "ERR-TIMEOUT":
        _time.sleep(30)
        return (408, operation_outcome(408, "Slow response timeout", order_id))

    if order_id == "ERR-DUPLICATE-ORDER":
        if order_id in _seen_order_ids:
            return (409, operation_outcome(409, "Duplicate order same day", order_id))
        _seen_order_ids.add(order_id)
        return None

    if order_id == "ERR-DUPLICATE-RESULT":
        if order_id in _seen_order_ids:
            return (409, operation_outcome(409, "DiagnosticReport sent twice", order_id))
        _seen_order_ids.add(order_id)
        return None

    triggers = {
        "ERR-RESULT-BEFORE-AUTH": (422, "Result released before authorization"),
        "ERR-CANCEL-RACE": (409, "Cancel during processing"),
        "ERR-CUTOFF": (422, "Order placed after daily cutoff"),
    }

    if order_id in triggers:
        http_code, message = triggers[order_id]
        return (http_code, operation_outcome(http_code, message, order_id))

    if order_id == "ERR-AMENDED":
        return (200, {"resourceType": "DiagnosticReport", "amended": True, "status": "amended"})

    return None
