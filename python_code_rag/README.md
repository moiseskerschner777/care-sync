Base URL: `http://localhost:8001`
Porta: http://localhost:52773/csp/sys/UtilHome.csp

## Running locally (venv)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

## Running with Docker

```bash
docker compose up --build
```


## Database connection (DBeaver)

JDBC URL: `jdbc:IRIS://localhost:1972/USER`

| Setting   | Value      |   |
|-----------|------------|---|
| Host      | localhost  |   |
| Port      | 1972       |   |
| Namespace | USER       |   |
| Username  | _SYSTEM    |   |
| Password  | SYS        |   |

Tables are created under the `labcore` schema:
`patient`, `practitioner`, `service_request`, `service_request_item`, `exam_catalog`

## MCP server (LLM integration)

The project exposes an MCP (Model Context Protocol) server that LLM clients — Claude Desktop, Continue, Cline, etc. — can connect to for semantic code search.

### Tools available to the LLM

| Tool | Description |
|------|-------------|
| `search_code` | Semantic search across indexed codebases |
| `list_collections` | List all indexed collections |
| `index_codebase` | Index a Python codebase directory |
| `health_check` | Check IRIS + Ollama connectivity |

### Claude Desktop config

Add this to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "python-code-rag": {
      "command": "docker",
      "args": ["compose", "-f", "/home/moises.kerschner/Documents/moises/python_code_rag/docker-compose.yml", "exec", "-T", "app", "python", "-m", "mcp_server"]
    }
  }
}
```

The container must be running first (`docker compose up -d`).

### Running the MCP server standalone

```bash
# from inside the running container
docker compose exec app python -m mcp_server

# or via docker compose run (starts a separate container)
docker compose run --rm app python -m mcp_server
```

## Generated API docs

FastAPI also exposes the generated API documentation at:

- `http://localhost:8001/docs`
- `http://localhost:8001/redoc`
- `http://localhost:8001/openapi.json`
