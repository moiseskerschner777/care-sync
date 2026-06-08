import logging
from datetime import datetime

from models.mapping_cache import MappingCache

logger = logging.getLogger(__name__)


def get_mapping(db, operation: str, system_target: str):
    result = db.query(MappingCache).filter(
        MappingCache.operation == operation,
        MappingCache.system_target == system_target,
    ).first()
    logger.info(
        "cache: %s | %s → %s",
        "hit" if result else "miss",
        operation,
        system_target,
    )
    return result


def save_mapping(db, operation: str, system_target: str, payload_schema: str,
                 example_request: str = None, example_response: str = None):
    import uuid
    schema_preview = payload_schema[:100] if payload_schema else ""
    logger.debug(
        "cache save operation=%s system_target=%s payload_schema_preview=%s",
        operation,
        system_target,
        schema_preview,
    )
    entry = MappingCache(
        id=str(uuid.uuid4()),
        operation=operation,
        system_target=system_target,
        payload_schema=payload_schema,
        example_request=example_request,
        example_response=example_response,
        use_count=0,
        created_at=datetime.utcnow(),
    )
    db.add(entry)
    db.commit()
    return entry


def update_usage(db, mapping_id: str):
    entry = db.query(MappingCache).filter(MappingCache.id == mapping_id).first()
    if entry:
        entry.use_count = (entry.use_count or 0) + 1
        entry.last_used_at = datetime.utcnow()
        db.commit()
        logger.debug("cache update id=%s new_use_count=%d", mapping_id, entry.use_count)
        return entry.use_count
    return 0
