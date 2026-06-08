from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health():
    return {"status": "ok", "system": "vitacare", "protocol": "proprietary-rest"}
