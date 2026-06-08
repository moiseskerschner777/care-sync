from fastapi import APIRouter
from fastapi import status
from fastapi.responses import JSONResponse
from sqlalchemy import text

from database import SessionLocal

router = APIRouter()


@router.get("/health")
def health_check():
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "error", "database": "unreachable"},
        )
    finally:
        db.close()
