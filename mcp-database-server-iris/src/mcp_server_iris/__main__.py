import argparse
import uvicorn


def run():
    parser = argparse.ArgumentParser(description="InterSystems IRIS MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "http"],
        default="stdio",
        help="Transport protocol to use (default: stdio)",
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host for HTTP transport (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=3001,
        help="Port for HTTP transport (default: 3001)",
    )
    args = parser.parse_args()

    if args.transport == "http":
        from mcp_server_iris.http_server import starlette_app
        uvicorn.run(starlette_app, host=args.host, port=args.port)
    else:
        from mcp_server_iris.server import run as run_stdio
        run_stdio()


run()
