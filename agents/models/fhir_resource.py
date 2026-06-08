import datetime
import uuid

from sqlalchemy import Column, DateTime, String, Text

from database import Base


class FHIRResource(Base):
    __tablename__ = "agent_fhir_resource"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    resource_type = Column(String(64), nullable=False, index=True)
    resource_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
