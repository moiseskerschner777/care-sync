from sqlalchemy import Column, ForeignKey, String

from database import Base


class ServiceRequestItem(Base):
    __tablename__ = "service_request_item"
    __table_args__ = {"schema": "labcore"}

    id = Column(String(36), primary_key=True)
    service_request_id = Column(
        String(36), ForeignKey("labcore.service_request.id"), nullable=False
    )
    exam_code = Column(String(20), nullable=False)
    exam_name = Column(String(120), nullable=False)
    status = Column(String(20), default="PENDING", nullable=False)
    notes = Column(String(255), nullable=True)
