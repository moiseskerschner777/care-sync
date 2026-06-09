import asyncio
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.chunker import chunk_codebase
from app.embedder import embed
from app import store
from app.retriever import collection_name

router = APIRouter()


class IndexRequest(BaseModel):
    path: str


@router.post("/index")
async def index(request: IndexRequest):
    target = Path(request.path)
    if not target.exists():
        raise HTTPException(400, f"Path '{request.path}' not found")

    collection = collection_name(request.path)
    chunks = chunk_codebase(target)
    vectors = await asyncio.to_thread(embed, [c.text for c in chunks])

    conn = store.get_connection()
    store.ensure_table(conn, collection)
    store.delete_collection(conn, collection)
    store.insert_chunks(conn, collection, chunks, vectors)
    conn.close()

    return {"collection": collection, "chunks_indexed": len(chunks), "status": "ok"}
