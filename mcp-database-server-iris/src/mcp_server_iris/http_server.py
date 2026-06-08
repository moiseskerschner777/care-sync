from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Route, Mount
from starlette.types import Scope, Receive, Send

from mcp_server_iris.server import server, _connect

_connect()

sse = SseServerTransport("/messages")


async def handle_sse(scope: Scope, receive: Receive, send: Send) -> Response:
    async with sse.connect_sse(scope, receive, send) as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )
    return Response()


async def sse_endpoint(request: Request) -> Response:
    return await handle_sse(request.scope, request.receive, request._send)


starlette_app = Starlette(
    routes=[
        Route("/sse", endpoint=sse_endpoint, methods=["GET"]),
        Mount("/messages", app=sse.handle_post_message),
    ]
)
