import json
import logging
import threading
from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import get_db
from models.exam_catalog import ExamCatalog
from models.service_request import ServiceRequest
from models.service_request_item import ServiceRequestItem
from schemas.service_request import ServiceRequestCreate, ServiceRequestResponse
from services.agent_trigger import resolve_targets, trigger_agent

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/{id}", response_model=ServiceRequestResponse)
def get_service_request(id: str, db: Session = Depends(get_db)):
    service_request = db.get(ServiceRequest, id)
    if service_request is None:
        raise HTTPException(status_code=404, detail="ServiceRequest not found")

    return service_request


@router.post("", response_model=ServiceRequestResponse, status_code=status.HTTP_201_CREATED)
def create_service_request(body: ServiceRequestCreate, db: Session = Depends(get_db)):
    max_code = db.query(func.max(ServiceRequest.code)).scalar()
    if max_code:
        next_number = int(max_code.split("-")[1]) + 1
    else:
        next_number = 1
    code = f"OS-{next_number:05d}"

    sr = ServiceRequest(
        id=str(uuid4()),
        code=code,
        status="ACTIVE",
        priority=body.priority,
        patient_id=body.patient_id,
        practitioner_id=body.practitioner_id,
        created_at=datetime.utcnow(),
        notes=body.notes,
    )
    db.add(sr)

    exam_codes = [item.exam_code for item in body.items]
    catalog_items = db.query(ExamCatalog).filter(ExamCatalog.exam_code.in_(exam_codes)).all()
    catalog_by_code = {c.exam_code: c for c in catalog_items}

    for item_data in body.items:
        exam_name = item_data.exam_name or catalog_by_code[item_data.exam_code].exam_name
        item = ServiceRequestItem(
            id=str(uuid4()),
            service_request_id=sr.id,
            exam_code=item_data.exam_code,
            exam_name=exam_name,
            status="PENDING",
        )
        db.add(item)

    db.commit()
    db.refresh(sr)

    sr_data = {
        "code": sr.code,
        "patient_id": sr.patient_id,
        "practitioner_id": sr.practitioner_id,
        "covenant_id": getattr(sr, "covenant_id", None),
        "cid_code": getattr(sr, "cid_code", None),
    }
    items_data = [
        {
            "exam_code": item.exam_code,
            "can_perform": item.can_perform,
            "support_lab": item.support_lab,
        }
        for item in catalog_items
    ]

    targets = resolve_targets(sr_data, items_data)
    logger.info("service_request created code=%s targets=%s", sr.code, targets)

    if targets:
        threading.Thread(target=trigger_agent, args=(sr_data, items_data), daemon=True).start()

    return sr


@router.put("/{id}/cancel", response_model=ServiceRequestResponse)
def cancel_service_request(id: str, db: Session = Depends(get_db)):
    service_request = db.get(ServiceRequest, id)
    if service_request is None:
        raise HTTPException(status_code=404, detail="ServiceRequest not found")

    if service_request.status == "CANCELLED":
        raise HTTPException(status_code=422, detail="ServiceRequest is already cancelled")

    service_request.status = "CANCELLED"
    service_request.cancelled_at = datetime.utcnow()

    for item in service_request.items:
        item.status = "CANCELLED"

    db.commit()
    db.refresh(service_request)

    return service_request
