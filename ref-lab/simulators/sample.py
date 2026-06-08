from simulators.error_response import operation_outcome


def check_sample(payload: dict):
    specimen_list = payload.get("specimen", [])
    if not specimen_list:
        return None
    specimen_ref = specimen_list[0].get("reference", "")
    if not specimen_ref.startswith("Specimen/"):
        return None
    sample_type = specimen_ref[len("Specimen/"):]

    triggers = {
        "ERR-TUBE": (422, "Wrong tube type"),
        "ERR-VOLUME": (422, "Insufficient sample volume"),
        "ERR-HEMOLYZED": (422, "Hemolyzed sample"),
        "ERR-EXPIRED": (422, "Sample expired"),
        "ERR-CUSTODY": (422, "Chain of custody broken"),
        "ERR-TEMPERATURE": (422, "Temperature deviation"),
    }

    if sample_type in triggers:
        http_code, message = triggers[sample_type]
        return (http_code, operation_outcome(http_code, message, sample_type))

    return None
