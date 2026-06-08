from simulators.error_response import rejected

TRIGGERS = {
    "ERR-EXPIRED": (403, "Covenant plan is not active"),
    "ERR-NOT-COVERED": (422, "Exam not covered by this plan"),
    "ERR-PATIENT-NOT-ENROLLED": (404, "Patient not found in VitaCare"),
    "ERR-AUTH-LIMIT": (429, "Daily authorization limit reached"),
    "ERR-REFERRAL": (422, "Referral from specialist required"),
    "ERR-JUSTIFICATION": (422, "Clinical justification text missing"),
    "ERR-AUTH-EXPIRED": (403, "Authorization expired before exam was performed"),
    "ERR-CID": (422, "CID code does not justify this exam"),
    "ERR-EXAM-LIMIT": (429, "Monthly exam limit reached for this patient"),
    "ERR-DOCTOR": (403, "Requesting physician not credentialed with this covenant"),
    "ERR-REFERRAL-SPECIALTY": (422, "Referral from wrong specialty"),
    "ERR-PLAN-DOWNGRADED": (403, "Patient plan downgraded — exam no longer covered"),
    "ERR-COPAY": (422, "Co-payment not collected at registration"),
    "ERR-TISS": (422, "TISS standard version mismatch"),
    "ERR-CRM": (403, "Doctor CRM not found in credentialed list"),
}


def simulate_covenant(covenant_id: str) -> tuple[int, dict] | None:
    if covenant_id in TRIGGERS:
        http_code, message = TRIGGERS[covenant_id]
        return (http_code, rejected(covenant_id, message, covenant_id))
    return None
