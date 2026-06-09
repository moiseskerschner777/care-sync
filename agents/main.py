import json
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import desc

from config import settings
from database import Base, SessionLocal, engine
from graph import graph
from memory.knowledge_base_indexer import index_knowledge_base
from models import knowledge_base, mapping_cache
from models.fhir_resource import FHIRResource
from routes.error_reports import router as error_reports_router

logging.getLogger("LiteLLM").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)

logging.basicConfig(
    level=logging.DEBUG if settings.app_env == "development" else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def _sanitized_settings() -> dict:
    s = settings.model_dump()
    for key in list(s.keys()):
        if "api_key" in key or "password" in key or "secret" in key:
            s[key] = "***"
    return s


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.debug("app startup — settings: %s", _sanitized_settings())

    Base.metadata.create_all(bind=engine)
    logger.debug("tables created")

    yield


app = FastAPI(title="MedBridge Agent", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://frontend:80"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(error_reports_router)


@app.post("/agent/invoke")
async def agent_invoke(body: dict):
    result = graph.invoke({
        "operation": body.get("operation"),
        "system_target": body.get("system_target"),
        "payload": body.get("payload", {}),
    })
    if result.get("error"):
        return {
            "status": "error",
            "operation": result["operation"],
            "system_target": result["system_target"],
            "cache_hit": result.get("cache_hit", False),
            "error": result["error"],
            "error_diagnosis": result.get("error_diagnosis"),
        }
    return {
        "status": "success",
        "operation": result["operation"],
        "system_target": result["system_target"],
        "cache_hit": result.get("cache_hit", False),
        "response": result.get("response"),
    }


@app.post("/fhir/r4/{resource_type}")
async def fhir_create(resource_type: str, request: Request):
    body = await request.json()
    resource_id = body.get("id") or body.get("resourceType", "").lower() + "-unknown"

    db = SessionLocal()
    try:
        resource = FHIRResource(
            id=resource_id,
            resource_type=resource_type,
            resource_json=json.dumps(body),
        )
        db.merge(resource)
        db.commit()
        logger.info("FHIR %s stored id=%s", resource_type, resource_id)
        return Response(
            content=json.dumps(body),
            media_type="application/fhir+json",
            status_code=201,
        )
    finally:
        db.close()


@app.get("/fhir/r4/{resource_type}")
async def fhir_search(
    resource_type: str,
    _count: int = Query(default=20, ge=1, le=100),
    _id: str = Query(default=None),
):
    db = SessionLocal()
    try:
        q = db.query(FHIRResource).filter(FHIRResource.resource_type == resource_type)
        if _id:
            q = q.filter(FHIRResource.id == _id)
        q = q.order_by(desc(FHIRResource.created_at)).limit(_count)
        rows = q.all()

        entries = []
        for row in rows:
            resource = json.loads(row.resource_json)
            entries.append({
                "fullUrl": f"{settings.fhir_base_url}/{resource_type}/{row.id}",
                "resource": resource,
            })

        bundle = {
            "resourceType": "Bundle",
            "type": "searchset",
            "total": len(entries),
            "entry": entries,
        }
        return Response(
            content=json.dumps(bundle),
            media_type="application/fhir+json",
        )
    finally:
        db.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
