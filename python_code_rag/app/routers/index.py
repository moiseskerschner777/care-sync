import asyncio, logging, traceback
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.chunker import chunk_codebase
from app.embedder import embed
from app import store
from app.retriever import collection_name

logger = logging.getLogger(__name__)

router = APIRouter()


class IndexRequest(BaseModel):
    path: str


@router.post("/index")
async def index(request: IndexRequest):
    target = Path(request.path)
    if not target.exists():
        raise HTTPException(400, f"Path '{request.path}' not found")

    collection = collection_name(request.path)
    logger.info("indexing path=%s collection=%s", request.path, collection)

    try:
        chunks = chunk_codebase(target)
        logger.info("chunked %d code chunks from %s", len(chunks), request.path)

        vectors = await asyncio.to_thread(embed, [c.text for c in chunks])
        logger.info("embedded %d vectors (dim=%d)", len(vectors), len(vectors[0]) if vectors else 0)

        conn = store.get_connection()
        store.ensure_table(conn, collection)
        store.delete_collection(conn, collection)
        logger.info("cleared existing data in collection %s", collection)
        store.insert_chunks(conn, collection, chunks, vectors)
        conn.close()

        logger.info("indexing complete for %s: %d chunks indexed", collection, len(chunks))
        return {"collection": collection, "chunks_indexed": len(chunks), "status": "ok"}
    except Exception as exc:
        logger.error("indexing FAILED for %s: %s", collection, exc)
        logger.error(traceback.format_exc())
        raise HTTPException(500, f"Indexing failed for '{request.path}': {exc}")
