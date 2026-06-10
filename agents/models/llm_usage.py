from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String

from database import Base


class LLMUsage(Base):
    __tablename__ = "agent_llm_usage"

    id = Column(Integer, primary_key=True, autoincrement=True)
    model = Column(String(100), nullable=False)
    operation = Column(String(50), nullable=True)
    system_target = Column(String(50), nullable=True)
    tokens_prompt = Column(Integer, default=0)
    tokens_completion = Column(Integer, default=0)
    tokens_total = Column(Integer, default=0)
    duration_ms = Column(Integer, default=0)
    success = Column(Boolean, default=True)
    error_msg = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
