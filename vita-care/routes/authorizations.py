import random
from datetime import datetime, timedelta

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from simulators.covenant import simulate_covenant
from simulators.pipeline import simulate

router = APIRouter()


@router.post("/authorizations")
async def post_authorization(request: Request):
    payload = await request.json()
    status_code, body = simulate(payload)
    return JSONResponse(content=body, status_code=status_code)


@router.get("/authorizations/{authorization_id}")
async def get_authorization(authorization_id: str):
    if authorization_id.startswith("ERR-"):
        trigger_result = simulate_covenant(authorization_id)
        if trigger_result is not None:
            status_code, body = trigger_result
            return JSONResponse(content=body, status_code=status_code)
    return JSONResponse(content={
        "authorization_id": authorization_id,
        "status": "approved",
        "valid_until": (datetime.utcnow() + timedelta(days=30)).isoformat() + "Z",
        "protocol": f"VITA-{random.randint(10000, 99999)}",
        "message": "Pre-authorization approved.",
    }, status_code=200)


@router.delete("/authorizations/{authorization_id}")
async def delete_authorization(authorization_id: str):
    if authorization_id.startswith("ERR-"):
        trigger_result = simulate_covenant(authorization_id)
        if trigger_result is not None:
            status_code, body = trigger_result
            return JSONResponse(content=body, status_code=status_code)
    return JSONResponse(content={
        "status": "cancelled",
        "authorization_id": authorization_id,
    }, status_code=200)
