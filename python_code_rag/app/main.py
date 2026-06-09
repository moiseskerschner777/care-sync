import asyncio, logging
from contextlib import asynccontextmanager
from pathlib import Path
import traceback

from fastapi import FastAPI

from app import store
from app.chunker import chunk_codebase
from app.embedder import embed
from app.retriever import collection_name
from app.routers import index

logger = logging.getLogger(__name__)

AUTO_INDEX_PATHS = ["/core-lab"]


async def _index_codebase(path: str) -> bool:
    target = Path(path)
    if not target.exists():
        logger.warning("[auto-index] path not found: %s", path)
        return False
    collection = collection_name(path)
    chunks = chunk_codebase(target)
    logger.info("[auto-index] chunked %d code blocks from %s", len(chunks), path)
    vectors = await asyncio.to_thread(embed, [c.text for c in chunks])
    logger.info("[auto-index] embedded %d vectors (dim=%d)", len(vectors), len(vectors[0]) if vectors else 0)
    conn = store.get_connection()
    store.ensure_table(conn, collection)
    store.delete_collection(conn, collection)
    logger.info("[auto-index] cleared collection %s", collection)
    store.insert_chunks(conn, collection, chunks, vectors)
    conn.close()
    logger.info("[auto-index] %s → collection=%s chunks=%d completed", path, collection, len(chunks))
    return True


@asynccontextmanager
async def lifespan(app: FastAPI):
    for path in AUTO_INDEX_PATHS:
        try:
            await _index_codebase(path)
        except Exception as e:
            logger.error("[auto-index] FAILED for %s: %s", path, e)
            logger.error(traceback.format_exc())
    yield


app = FastAPI(title="python-code-rag", lifespan=lifespan)
app.include_router(index.router)
