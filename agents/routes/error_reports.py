import json
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from database import SessionLocal, get_db
from graph import graph
from models.error_report import ErrorReport

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/error-reports")


class ErrorReportResponse(BaseModel):
    id: str
    created_at: datetime
    system_target: str
    operation: str
    origin: str
    confidence: float
    evidence: str
    suggestion: str
    payload_sent: str
    raw_error: str
    audit_event_id: str
    payload_hash: str | None
    raw_error_hash: str | None
    status: str

    model_config = ConfigDict(from_attributes=True)


@router.get("", response_model=list[ErrorReportResponse])
def list_error_reports(db: Session = Depends(get_db)):
    rows = (
        db.query(ErrorReport)
        .order_by(ErrorReport.created_at.desc())
        .all()
    )
    return rows


@router.post("/{id}/confirm-fix")
def confirm_fix(id: str):
    db = SessionLocal()
    try:
        row = db.query(ErrorReport).filter(ErrorReport.id == id).first()
        if row is None:
            raise HTTPException(status_code=404, detail="ErrorReport not found")

        payload = json.loads(row.payload_sent)

        result = graph.invoke({
            "operation": row.operation,
            "system_target": row.system_target,
            "payload": payload,
        })

        if result.get("error"):
            return {"status": "pending"}
        else:
            row.status = "fixed"
            db.commit()
            return {"status": "fixed"}
    finally:
        db.close()


@router.post("/{id}/dismiss")
def dismiss(id: str):
    db = SessionLocal()
    try:
        row = db.query(ErrorReport).filter(ErrorReport.id == id).first()
        if row is None:
            raise HTTPException(status_code=404, detail="ErrorReport not found")

        row.status = "dismissed"
        db.commit()
        return {"status": "dismissed"}
    finally:
        db.close()
