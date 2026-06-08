import hashlib
import logging
import os
import uuid
from datetime import datetime

import httpx

from config import settings

from tools.knowledge_base import _normalize_target

logger = logging.getLogger(__name__)


def _get_embedding(text: str) -> list:
    url = f"{settings.embedding_api_base}/api/embeddings"
    resp = httpx.post(
        url,
        json={"model": "nomic-embed-text", "prompt": text},
        timeout=30
    )
    resp.raise_for_status()
    return resp.json()["embedding"]


def _get_system_target(file_path: str) -> str:
    parts = file_path.replace("\\", "/").split("/")
    for i, part in enumerate(parts):
        if part == "knowledge" and i + 1 < len(parts):
            return parts[i + 1]
    return "unknown"


def _chunk_text(text: str, max_chars: int = 500):
    chunks = []
    current = ""
    for line in text.split("\n"):
        if len(current) + len(line) + 1 > max_chars and current:
            chunks.append(current.strip())
            current = ""
        current += line + "\n"
    if current.strip():
        chunks.append(current.strip())
    return chunks if chunks else [text.strip()]


def index_knowledge_base(db, system_target: str = None):
    knowledge_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "knowledge")
    if not os.path.exists(knowledge_dir):
        return 0, 0

    from models.knowledge_base import KnowledgeBase

    matching_files = []
    for root, dirs, files in os.walk(knowledge_dir):
        if system_target and _normalize_target(os.path.basename(root)) != _normalize_target(system_target):
            if root != knowledge_dir:
                continue
        for filename in files:
            if filename.endswith(".md"):
                matching_files.append(os.path.join(root, filename))

    if not matching_files:
        return 0, 0

    logger.info("→ indexing %s | files found: %d", system_target or "all", len(matching_files))

    total_inserted = 0
    total_skipped = 0

    for file_path in matching_files:
        filename = os.path.basename(file_path)
        logger.debug("reading file: %s", filename)
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        doc_hash = hashlib.md5(content.encode("utf-8")).hexdigest()

        existing = db.query(KnowledgeBase).filter(
            KnowledgeBase.doc_hash == doc_hash
        ).first()
        if existing:
            logger.debug("skipped (already indexed) source=%s hash=%s", filename, doc_hash)
            total_skipped += 1
            continue

        system_target = _get_system_target(file_path)
        rel_path = os.path.relpath(file_path, os.path.dirname(knowledge_dir))

        chunks = _chunk_text(content)

        try:
            logger.debug(
                "embedding provider=%s api_base=%s",
                settings.embedding_provider,
                settings.embedding_api_base
            )

            embedding_vector = _get_embedding(chunks[0])
        except Exception:
            logger.error("embedding generation failed for chunk", exc_info=True)
            embedding_vector = []

        for idx, chunk in enumerate(chunks):
            logger.debug("chunk index=%d preview=%s", idx, chunk[:50])
            entry = KnowledgeBase(
                id=str(uuid.uuid4()),
                system_target=system_target,
                source=rel_path,
                content=chunk,
                doc_hash=doc_hash,
                embedding=str(embedding_vector),
                created_at=datetime.utcnow(),
            )
            db.add(entry)
            total_inserted += 1

        db.commit()

    logger.info("✓ indexed %d chunks | skipped %d", total_inserted, total_skipped)
    return total_inserted, total_skipped
