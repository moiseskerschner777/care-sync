from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health():
    return {"status": "ok", "system": "reflab", "protocol": "FHIR R4"}
