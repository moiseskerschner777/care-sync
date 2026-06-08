from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ServiceRequestItemResponse(BaseModel):
    id: str
    service_request_id: str
    exam_code: str
    exam_name: str
    status: str
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ServiceRequestResponse(BaseModel):
    id: str
    code: str
    status: str
    priority: str
    patient_id: str
    practitioner_id: str
    created_at: datetime
    cancelled_at: Optional[datetime] = None
    notes: Optional[str] = None
    items: list[ServiceRequestItemResponse] = []

    model_config = ConfigDict(from_attributes=True)


class ServiceRequestItemCreate(BaseModel):
    exam_code: str
    exam_name: Optional[str] = None
    notes: Optional[str] = None


class ServiceRequestCreate(BaseModel):
    patient_id: str
    practitioner_id: str
    priority: str = "ROUTINE"
    notes: Optional[str] = None
    items: list[ServiceRequestItemCreate]
