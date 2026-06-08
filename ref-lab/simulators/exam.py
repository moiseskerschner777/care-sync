from simulators.error_response import operation_outcome
from simulators.pipeline import extract_exam_code


def check_exam(payload: dict):
    exam_code = extract_exam_code(payload)
    if not exam_code:
        return None

    triggers = {
        "ERR-LOINC": (404, "LOINC code unknown in RefLab catalog"),
        "ERR-FASTING": (422, "Fasting flag missing"),
        "ERR-CLINICAL-INFO": (422, "Required clinical info absent"),
        "ERR-INCOMPATIBLE": (422, "Incompatible exam combination"),
        "ERR-DISCONTINUED": (410, "Exam discontinued"),
        "ERR-METHODOLOGY": (422, "Methodology mismatch"),
        "ERR-CRITICAL-FLAG": (422, "Critical value not flagged"),
        "ERR-FORMAT": (422, "Exam code wrong format (HEM001 vs HEM-001)"),
        "ERR-CBHPM": (422, "Exam not in CBHPM table"),
    }

    if exam_code in triggers:
        http_code, message = triggers[exam_code]
        return (http_code, operation_outcome(http_code, message, exam_code))

    return None
