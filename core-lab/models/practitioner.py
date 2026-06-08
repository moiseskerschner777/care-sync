from sqlalchemy import Boolean, Column, String

from database import Base


class Practitioner(Base):
    __tablename__ = "practitioner"
    __table_args__ = {"schema": "labcore"}

    id = Column(String(36), primary_key=True)
    name = Column(String(120), nullable=False)
    specialty = Column(String(80), nullable=False)
    council_type = Column(String(10), nullable=False)
    council_number = Column(String(30), nullable=False)
    council_state = Column(String(2), nullable=False)
    active = Column(Boolean, default=True, nullable=False)
