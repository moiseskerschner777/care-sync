import argparse

import uvicorn


def run():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--transport",
        choices=["stdio", "http"],
        default="stdio",
    )
    args = parser.parse_args()

    if args.transport == "http":
        from mcp_server.http_server import starlette_app
        uvicorn.run(starlette_app, host="0.0.0.0", port=8005)
    else:
        from mcp_server.server import run as run_stdio
        run_stdio()


run()
