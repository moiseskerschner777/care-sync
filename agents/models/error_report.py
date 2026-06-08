from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Index, String, Text

from database import Base


class ErrorReport(Base):
    __tablename__ = "agent_error_report"

    id = Column(String(36), primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    system_target = Column(String(50), nullable=False)
    operation = Column(String(100), nullable=False)
    origin = Column(String(20), nullable=False)
    confidence = Column(Float, nullable=False)
    evidence = Column(Text, nullable=False)
    suggestion = Column(Text, nullable=False)
    payload_sent = Column(Text, nullable=False)
    raw_error = Column(Text, nullable=False)
    audit_event_id = Column(String(36), nullable=False)
    payload_hash = Column(String(64), nullable=True)
    raw_error_hash = Column(String(64), nullable=True)

    __table_args__ = (
        Index(
            "ix_error_report_dedup",
            "operation",
            "system_target",
            "payload_hash",
            "raw_error_hash",
        ),
    )
