from simulators.error_response import operation_outcome

_FORMAT_TRIGGERS = {
    "ERR-DECIMAL": (422, "Decimal separator mismatch"),
    "ERR-TIMEZONE": (422, "Timezone mismatch in timestamp"),
    "ERR-NULL": (422, "Empty string where null expected"),
    "ERR-BOOL": (422, "Boolean sent as string"),
    "ERR-OVERFLOW": (422, "Integer overflow"),
    "ERR-TRUNCATED": (422, "Field truncated"),
}


def _find_trigger(value, triggers):
    if isinstance(value, str) and value in triggers:
        return value
    return None


def _scan_payload(obj, triggers):
    if isinstance(obj, dict):
        for _, v in obj.items():
            result = _scan_payload(v, triggers)
            if result is not None:
                return result
    elif isinstance(obj, list):
        for item in obj:
            result = _scan_payload(item, triggers)
            if result is not None:
                return result
    elif isinstance(obj, str):
        return _find_trigger(obj, triggers)
    return None


def check_format(payload: dict):
    trigger = _scan_payload(payload, _FORMAT_TRIGGERS)
    if trigger is not None:
        http_code, message = _FORMAT_TRIGGERS[trigger]
        return (http_code, operation_outcome(http_code, message, trigger))
    return None
