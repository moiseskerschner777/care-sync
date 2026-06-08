from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from simulators.pipeline import simulate
from simulators.cancellation import simulate_cancel

router = APIRouter()


@router.post("/ServiceRequest")
async def create_service_request(request: Request):
    payload = await request.json()
    status_code, body = simulate(payload)
    return JSONResponse(content=body, status_code=status_code)


@router.delete("/ServiceRequest/{id}")
async def cancel_service_request(id: str):
    status_code, body = simulate_cancel(id)
    return JSONResponse(content=body, status_code=status_code)
