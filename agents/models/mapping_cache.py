from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from database import Base


class MappingCache(Base):
    __tablename__ = "agent_mapping_cache"

    id = Column(String(36), primary_key=True)
    operation = Column(String(100), nullable=False)
    system_target = Column(String(100), nullable=False)
    payload_schema = Column(Text, nullable=False)
    example_request = Column(Text)
    example_response = Column(Text)
    use_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_used_at = Column(DateTime, nullable=True)
