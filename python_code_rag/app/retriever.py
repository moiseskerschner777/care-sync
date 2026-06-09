import re, logging
from pathlib import Path

from app.embedder import embed
from app import store

from app.config import MIN_SCORE_THRESHOLD

logger = logging.getLogger(__name__)

SCHEMA_SCORE_PENALTY = -0.15


def collection_name(path: str) -> str:
    name = Path(path).name.lower()
    return re.sub(r"[^a-z0-9]", "_", name)


def retrieve(query: str, collection: str, top_k: int) -> list[dict]:
    logger.info("retrieve: query=%r collection=%r top_k=%d", query, collection, top_k)
    vector = embed([query])[0]
    conn = store.get_connection()
    results = store.search(conn, collection, vector, top_k * 3)
    conn.close()

    for r in results:
        if r["type"] == "schema":
            r["score"] += SCHEMA_SCORE_PENALTY

    results.sort(key=lambda r: r["score"], reverse=True)

    results = [r for r in results if r["score"] >= MIN_SCORE_THRESHOLD]

    top = results[:top_k]
    logger.info("retrieve: %d results after score filtering (threshold=%.2f), returning top %d",
                len(results), MIN_SCORE_THRESHOLD, len(top))
    for i, r in enumerate(top):
        logger.info("  #%d score=%.4f file=%s type=%s name=%s", i + 1, r["score"], r["file"], r["type"], r["name"])

    return top
