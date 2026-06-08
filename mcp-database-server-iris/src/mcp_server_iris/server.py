import os
import asyncio
import logging
import iris as irisnative
import mcp.types as types
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from mcp_server_iris import interoperability

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

server = Server("InterSystems IRIS MCP Server")

# Module-level connection objects — set during startup before the server loop
_db = None
_iris = None


def _connect():
    global _db, _iris
    config = {
        "hostname": os.getenv("IRIS_HOSTNAME"),
        "port": int(os.getenv("IRIS_PORT", 1972)),
        "namespace": os.getenv("IRIS_NAMESPACE", "USER"),
        "username": os.getenv("IRIS_USERNAME"),
        "password": os.getenv("IRIS_PASSWORD"),
    }
    if not all([config["hostname"], config["username"], config["password"]]):
        raise ValueError("Missing required IRIS connection environment variables")
    logger.info(
        f"Connecting to IRIS: iris://{config['username']}:{'x'*8}@{config['hostname']}:{config['port']}/{config['namespace']}"
    )
    _db = irisnative.connect(sharedmemory=False, **config)
    _iris = irisnative.createIRIS(_db)
    logger.info("Connected to IRIS")


# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------

_EXECUTE_SQL_TOOL = Tool(
    name="execute_sql",
    description="Execute an SQL query on the IRIS server",
    inputSchema={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "SQL query to execute"},
            "params": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Query parameters",
                "default": [],
            },
        },
        "required": ["query"],
    },
)


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [_EXECUTE_SQL_TOOL] + interoperability.list_tools()


# ---------------------------------------------------------------------------
# Tool dispatch
# ---------------------------------------------------------------------------

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "execute_sql":
        return await _handle_execute_sql(arguments)
    else:
        return await interoperability.call_tool(name, arguments, _iris, _db)


async def _handle_execute_sql(args: dict) -> list[TextContent]:
    query = args["query"]
    params = args.get("params", [])
    logger.info(f"Executing SQL: {query}")
    with _db.cursor() as cursor:
        cursor.execute(query, params)
        rows = cursor.fetchall()[:100]
    return [TextContent(type="text", text=str(rows))]


# ---------------------------------------------------------------------------
# Entry points
# ---------------------------------------------------------------------------

async def main():
    _connect()
    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())


def run():
    asyncio.run(main())
