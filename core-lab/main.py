import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
import uvicorn

from config import settings
from database import Base, SessionLocal, create_schema_if_not_exists, engine
from models import exam_catalog, patient, practitioner, service_request, service_request_item
from routes.health import router as health_router
from routes.patients import router as patients_router
from routes.practitioners import router as practitioners_router
from routes.exam_catalog import router as exam_catalog_router
from routes.service_requests import router as service_requests_router
from seed.seed_data import seed_database_if_empty

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

logging.basicConfig(
    level=logging.DEBUG if settings.app_env == "development" else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

if os.getenv("DEBUG_PORT"):
    try:
        import socket
        s = socket.create_connection(('172.17.0.1', int(os.getenv("DEBUG_PORT", "5678"))), timeout=2)
        s.close()
        import pydevd_pycharm
        pydevd_pycharm.settrace(
            '172.17.0.1',
            port=int(os.getenv("DEBUG_PORT", "5678")),
            stdout_to_server=True,
            stderr_to_server=True,
            suspend=False
        )
    except (ConnectionRefusedError, OSError):
        print("⚠️  PyCharm debugger not available, starting without debug")

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_schema_if_not_exists(engine)
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        seed_database_if_empty(session)
    finally:
        session.close()
    yield


app = FastAPI(title="LabCore API", version="0.1.0", lifespan=lifespan)
app.include_router(health_router)
app.include_router(patients_router, prefix="/patients")
app.include_router(practitioners_router, prefix="/practitioners")
app.include_router(exam_catalog_router, prefix="/exam-catalog")
app.include_router(service_requests_router, prefix="/service-requests")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
