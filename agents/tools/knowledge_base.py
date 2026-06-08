import ast
import concurrent.futures
import logging
import time

from litellm import embedding

from config import settings
from models.knowledge_base import KnowledgeBase

logger = logging.getLogger(__name__)


def _embed_sync(model: str, input: list[str], api_base: str | None):
    """Run embedding synchronously, dispatching to a thread if an event loop is running."""
    try:
        import asyncio
        asyncio.get_running_loop()
    except RuntimeError:
        return embedding(model=model, input=input, api_base=api_base)
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(embedding, model=model, input=input, api_base=api_base).result()


def _normalize_target(name: str) -> str:
    return name.replace("-", "")


def search_knowledge_base(db, system_target: str, query: str, top_k: int = 5) -> list[str]:
    normalized = _normalize_target(system_target)
    all_docs = db.query(KnowledgeBase).all()
    docs = [doc for doc in all_docs if _normalize_target(doc.system_target) == normalized]

    if not docs:
        return []

    model = settings.embedding_provider
    logger.debug("embedding generation started model=%s input_length=%d", model, len(query))
    start = time.time()
    try:
        emb_response = _embed_sync(
            model,
            [query],
            settings.embedding_api_base or None,
        )
        query_embedding = emb_response["data"][0]["embedding"]
        elapsed = time.time() - start
        logger.debug("embedding generation finished vector_size=%d time_taken=%.2fs", len(query_embedding), elapsed)
    except Exception:
        elapsed = time.time() - start
        logger.debug("embedding generation failed time_taken=%.2fs — falling back to top-k", elapsed)
        logger.debug("SQL query executed top_k=%d system_target=%s results=%d (fallback)", top_k, system_target, min(top_k, len(docs)))
        return [doc.content for doc in docs[:top_k]]

    if not query_embedding:
        logger.debug("SQL query executed top_k=%d system_target=%s results=%d (no embedding)", top_k, system_target, min(top_k, len(docs)))
        return [doc.content for doc in docs[:top_k]]

    results = []
    for doc in docs:
        try:
            doc_embedding = ast.literal_eval(doc.embedding or "[]")
        except (ValueError, SyntaxError):
            continue

        if not doc_embedding:
            continue

        similarity = sum(a * b for a, b in zip(query_embedding, doc_embedding))
        results.append((similarity, doc.content))

    results.sort(key=lambda x: x[0], reverse=True)
    final = [content for _, content in results[:top_k]]
    logger.debug("SQL query executed top_k=%d system_target=%s results=%d", top_k, system_target, len(final))
    return final
