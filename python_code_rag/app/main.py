import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from app import store
from app.chunker import chunk_codebase
from app.embedder import embed
from app.retriever import collection_name
from app.routers import index

AUTO_INDEX_PATHS = ["/core-lab"]


async def _index_codebase(path: str) -> bool:
    target = Path(path)
    if not target.exists():
        print(f"[auto-index] path not found: {path}")
        return False
    collection = collection_name(path)
    chunks = chunk_codebase(target)
    vectors = await asyncio.to_thread(embed, [c.text for c in chunks])
    conn = store.get_connection()
    store.ensure_table(conn, collection)
    store.delete_collection(conn, collection)
    store.insert_chunks(conn, collection, chunks, vectors)
    conn.close()
    print(f"[auto-index] {path} → collection={collection} chunks={len(chunks)}")
    return True


@asynccontextmanager
async def lifespan(app: FastAPI):
    for path in AUTO_INDEX_PATHS:
        try:
            await _index_codebase(path)
        except Exception as e:
            print(f"[auto-index] failed for {path}: {e}")
    yield


app = FastAPI(title="python-code-rag", lifespan=lifespan)
app.include_router(index.router)
