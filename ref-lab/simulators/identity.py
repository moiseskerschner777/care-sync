from simulators.error_response import operation_outcome
from simulators.pipeline import extract_patient_id


def check_identity(payload: dict):
    patient_id = extract_patient_id(payload)
    if not patient_id:
        return None

    triggers = {
        "ERR-ACCENT": (422, "Patient name has accent — normalized version does not match"),
        "ERR-DOC-TYPE": (422, "CPF vs RG document type conflict"),
        "ERR-DOB-FORMAT": (422, "Date of birth format mismatch"),
        "ERR-DUPLICATE": (409, "Duplicate patient record in RefLab"),
        "ERR-GENDER": (422, "Gender format mismatch (M vs male)"),
        "ERR-MINOR": (422, "Underage patient missing guardian data"),
        "ERR-CPF": (422, "CPF check digit validation failure"),
        "ERR-ENCODING": (422, "Special characters corrupted in transit"),
    }

    if patient_id in triggers:
        http_code, message = triggers[patient_id]
        return (http_code, operation_outcome(http_code, message, patient_id))

    return None
