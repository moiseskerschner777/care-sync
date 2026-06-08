FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy source and install the MCP server package
COPY src/ /app/src/
COPY pyproject.toml /app/
COPY README.md /app/

RUN uv pip install --system --no-cache .

# Copy example files
COPY example/mcp-server.py /app/example/mcp-server.py
COPY example/requirements-dev.txt /app/example/requirements-dev.txt

# Install example dependencies
RUN uv pip install --system --no-cache -r /app/example/requirements-dev.txt

# Environment variables for IRIS connection
ENV IRIS_HOSTNAME=iris
ENV IRIS_PORT=1972
ENV IRIS_NAMESPACE=USER
ENV IRIS_USERNAME=_SYSTEM
ENV IRIS_PASSWORD=SYS

WORKDIR /app/example

CMD ["python", "mcp-server.py"]
