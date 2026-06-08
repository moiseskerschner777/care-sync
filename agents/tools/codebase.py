import asyncio
import json
import logging

from config import settings

logger = logging.getLogger(__name__)

COLLECTION_NAME = None


async def _list_collections():
    from mcp import ClientSession
    from mcp.client.sse import sse_client

    async with sse_client(settings.codebase_mcp_url) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool("list_collections", {})
            return result


def get_labcore_collection() -> str:
    global COLLECTION_NAME
    if COLLECTION_NAME is not None:
        return COLLECTION_NAME

    result = asyncio.run(_list_collections())
    raw = result.content[0].text if result.content else ""
    data = json.loads(raw)
    collections = data.get("collections", [])
    if not collections:
        raise RuntimeError("No collections found in python-code-rag")

    for name in collections:
        if "labcore" in name.lower() or "core_lab" in name.lower():
            COLLECTION_NAME = name
            return name

    COLLECTION_NAME = collections[0]
    return collections[0]


async def _search_code(collection: str, query: str, top_k: int):
    from mcp import ClientSession
    from mcp.client.sse import sse_client

    async with sse_client(settings.codebase_mcp_url) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool("search_code", {
                "collection": collection,
                "query": query,
                "top_k": top_k,
            })
            return result


def search_labcore_code(query: str, top_k: int = 8) -> list[str]:
    try:
        collection = get_labcore_collection()
        result = asyncio.run(_search_code(collection, query, top_k))
    except Exception:
        logger.warning("python-code-rag MCP unreachable — returning empty results", exc_info=True)
        return []
    if not result.content:
        return []
    raw = result.content[0].text
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return [raw]
    if isinstance(data, list):
        chunks = []
        for item in data:
            if isinstance(item, str):
                chunks.append(item)
            elif isinstance(item, dict):
                chunks.append(item.get("text", json.dumps(item, default=str)))
        return chunks
    if isinstance(data, dict) and "results" in data:
        return [item.get("text", str(item)) for item in data["results"]]
    if isinstance(data, dict) and "error" in data:
        return []
    return [raw]
