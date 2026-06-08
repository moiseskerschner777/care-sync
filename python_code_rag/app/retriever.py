import re
from pathlib import Path

from app.embedder import embed
from app import store

from app.config import MIN_SCORE_THRESHOLD

SCHEMA_SCORE_PENALTY = -0.15


def collection_name(path: str) -> str:
    name = Path(path).name.lower()
    return re.sub(r"[^a-z0-9]", "_", name)


def retrieve(query: str, collection: str, top_k: int) -> list[dict]:
    vector = embed([query])[0]
    conn = store.get_connection()
    results = store.search(conn, collection, vector, top_k * 3)
    conn.close()

    for r in results:
        if r["type"] == "schema":
            r["score"] += SCHEMA_SCORE_PENALTY

    results.sort(key=lambda r: r["score"], reverse=True)

    results = [r for r in results if r["score"] >= MIN_SCORE_THRESHOLD]

    return results[:top_k]
