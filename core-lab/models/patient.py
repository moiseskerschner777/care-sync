from datetime import datetime

from sqlalchemy import Boolean, Column, Date, DateTime, String

from database import Base


class Patient(Base):
    __tablename__ = "patient"
    __table_args__ = {"schema": "labcore"}

    id = Column(String(36), primary_key=True)
    name_family = Column(String(120), nullable=False)
    name_given = Column(String(120), nullable=False)
    birth_date = Column(Date, nullable=False)
    gender = Column(String(20), nullable=False)
    active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
