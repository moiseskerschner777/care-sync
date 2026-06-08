#!/bin/bash
uvicorn app.main:app --host 0.0.0.0 --port 8001 &
python -m mcp_server --transport http
