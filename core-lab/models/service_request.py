from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship

from database import Base


class ServiceRequest(Base):
    __tablename__ = "service_request"
    __table_args__ = {"schema": "labcore"}

    id = Column(String(36), primary_key=True)
    code = Column(String(20), unique=True, nullable=False)
    status = Column(String(20), default="ACTIVE", nullable=False)
    priority = Column(String(20), default="ROUTINE", nullable=False)
    patient_id = Column(String(36), ForeignKey("labcore.patient.id"), nullable=False)
    practitioner_id = Column(
        String(36), ForeignKey("labcore.practitioner.id"), nullable=False
    )
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    cancelled_at = Column(DateTime, nullable=True)
    notes = Column(String(255), nullable=True)

    patient = relationship("Patient")
    practitioner = relationship("Practitioner")
    items = relationship("ServiceRequestItem")
