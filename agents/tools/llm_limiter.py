import logging
from typing import Any, Dict, Optional

from sqlalchemy import func

from config import settings
from database import SessionLocal
from models.llm_usage import LLMUsage

logger = logging.getLogger(__name__)


def check_limits(state: Dict[str, Any]) -> bool:
    max_tokens = settings.llm_provider_max_tokens
    if max_tokens <= 0:
        return False

    db = SessionLocal()
    try:
        total = db.query(func.coalesce(func.sum(LLMUsage.tokens_total), 0)).scalar()
        if total >= max_tokens:
            state["rate_limited"] = True
            state["error"] = {
                "http_code": 429,
                "body": f"LLM token limit reached ({total}/{max_tokens} tokens). No further calls allowed.",
            }
            logger.warning("LLM rate limited: %d/%d tokens used", total, max_tokens)
            return True
        logger.debug("LLM token usage: %d/%d", total, max_tokens)
        return False
    finally:
        db.close()


def record_usage(
    state: Dict[str, Any],
    tokens_usage: Optional[Dict[str, int]],
    duration_ms: int,
    success: bool,
    error_msg: Optional[str] = None,
) -> None:
    db = SessionLocal()
    try:
        usage = tokens_usage or {}
        row = LLMUsage(
            model=settings.llm_provider,
            operation=state.get("operation"),
            system_target=state.get("system_target"),
            tokens_prompt=usage.get("prompt_tokens", 0),
            tokens_completion=usage.get("completion_tokens", 0),
            tokens_total=usage.get("total_tokens", 0),
            duration_ms=int(duration_ms * 1000),
            success=success,
            error_msg=error_msg[:500] if error_msg else None,
        )
        db.add(row)
        db.commit()
    finally:
        db.close()
