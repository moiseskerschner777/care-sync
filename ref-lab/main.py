import logging

from fastapi import FastAPI

from config import settings
from routes.health import router as health_router
from routes.service_requests import router as service_requests_router
from routes.diagnostic_reports import router as diagnostic_reports_router

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

logging.basicConfig(
    level=logging.DEBUG if settings.app_env == "development" else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

app = FastAPI(title="RefLab API", version="0.1.0")

app.include_router(health_router)
app.include_router(service_requests_router, prefix="/fhir/r4")
app.include_router(diagnostic_reports_router, prefix="/fhir/r4")
