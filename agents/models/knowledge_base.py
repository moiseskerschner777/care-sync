from datetime import datetime

from sqlalchemy import Column, DateTime, String, Text

from database import Base


class KnowledgeBase(Base):
    __tablename__ = "agent_knowledge_base"

    id = Column(String(36), primary_key=True)
    system_target = Column(String(100), nullable=False)
    source = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    doc_hash = Column(String(64), nullable=False)
    embedding = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
