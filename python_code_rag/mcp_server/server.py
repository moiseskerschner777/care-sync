import asyncio
import json, logging
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from app import store, config
from app.chunker import chunk_codebase
from app.embedder import embed as sync_embed
from app.retriever import retrieve as sync_retrieve, collection_name

logger = logging.getLogger(__name__)

server = Server("python-code-rag")


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="search_code",
            description=(
                "Search indexed Python codebases using semantic search. "
                "Returns matching functions, classes, modules, and imports ranked by relevance. "
                "Use this to find code related to a natural language query."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "collection": {
                        "type": "string",
                        "description": "Name of the indexed collection to search (use list_collections to discover available ones).",
                    },
                    "query": {
                        "type": "string",
                        "description": "Natural language query describing the code you want to find.",
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Number of results to return (default: 8).",
                        "default": 8,
                    },
                },
                "required": ["collection", "query"],
            },
        ),
        Tool(
            name="list_collections",
            description="List all indexed Python codebase collections available for semantic search.",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="index_codebase",
            description=(
                "Index a Python codebase directory for semantic search. "
                "Chunks all .py files using tree-sitter AST analysis and embeds them for retrieval. "
                "This must be called before search_code for a given codebase."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Absolute path to the Python codebase directory to index.",
                    },
                },
                "required": ["path"],
            },
        ),
        Tool(
            name="health_check",
            description=(
                "Check if the RAG backend services (IRIS vector database and Ollama embeddings server) "
                "are healthy and reachable."
            ),
            inputSchema={"type": "object", "properties": {}},
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    logger.info("MCP tool called: %s args=%s", name, arguments)
    if name == "search_code":
        return await _handle_search(arguments)
    elif name == "list_collections":
        return await _handle_list_collections()
    elif name == "index_codebase":
        return await _handle_index(arguments)
    elif name == "health_check":
        return await _handle_health()
    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def _handle_search(args: dict) -> list[TextContent]:
    collection = args["collection"]
    query = args["query"]
    top_k = args.get("top_k", config.SEARCH_TOP_K)

    conn = store.get_connection()
    if not store.collection_exists(conn, collection):
        conn.close()
        return [
            TextContent(
                type="text",
                text=json.dumps({
                    "error": f"Collection '{collection}' not found.",
                    "hint": "Use list_collections to see available collections.",
                }, indent=2),
            )
        ]
    conn.close()

    results = await asyncio.to_thread(sync_retrieve, query, collection, top_k)
    return [TextContent(type="text", text=json.dumps(results, indent=2, ensure_ascii=False, default=str))]


async def _handle_list_collections() -> list[TextContent]:
    conn = store.get_connection()
    cols = store.list_collections(conn)
    conn.close()
    return [TextContent(type="text", text=json.dumps({"collections": cols}, indent=2))]


async def _handle_index(args: dict) -> list[TextContent]:
    target = Path(args["path"])
    if not target.exists():
        return [
            TextContent(
                type="text",
                text=json.dumps({"error": f"Path '{args['path']}' not found."}, indent=2),
            )
        ]

    collection = collection_name(args["path"])
    chunks = chunk_codebase(target)
    texts = [c.text for c in chunks]

    vectors = await asyncio.to_thread(sync_embed, texts)

    conn = store.get_connection()
    store.ensure_table(conn, collection)
    store.delete_collection(conn, collection)
    store.insert_chunks(conn, collection, chunks, vectors)
    conn.close()

    return [
        TextContent(
            type="text",
            text=json.dumps({
                "collection": collection,
                "chunks_indexed": len(chunks),
                "status": "ok",
            }, indent=2),
        )
    ]


async def _handle_health() -> list[TextContent]:
    import httpx

    result = {"status": "ok", "iris": "ok", "ollama": "ok"}

    try:
        conn = store.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.fetchone()
        conn.close()
        logger.info("health_check: IRIS connection OK")
    except Exception as e:
        result["iris"] = str(e)
        result["status"] = "degraded"
        logger.warning("health_check: IRIS connection FAILED — %s", e)

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{config.OLLAMA_URL}/api/tags", timeout=3.0)
            resp.raise_for_status()
            logger.info("health_check: Ollama %s OK", config.OLLAMA_URL)
    except Exception as e:
        result["ollama"] = str(e)
        result["status"] = "degraded"
        logger.warning("health_check: Ollama %s FAILED — %s", config.OLLAMA_URL, e)

    return [TextContent(type="text", text=json.dumps(result, indent=2))]


async def main():
    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())


def run():
    asyncio.run(main())
