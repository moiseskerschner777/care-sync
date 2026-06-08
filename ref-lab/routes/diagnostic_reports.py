import uuid
from datetime import datetime, timezone

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()


@router.get("/DiagnosticReport/{id}")
async def get_diagnostic_report(id: str):
    body = {
        "resourceType": "DiagnosticReport",
        "id": id,
        "status": "final",
        "code": {
            "coding": [{
                "system": "http://loinc.org",
                "code": "simulated",
                "display": "Simulated Result",
            }]
        },
        "subject": {
            "reference": "Patient/simulated-patient"
        },
        "issued": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "conclusion": "Simulated diagnostic report.",
        "result": [{
            "reference": "Observation/simulated-001"
        }],
    }
    return JSONResponse(content=body, status_code=200)
