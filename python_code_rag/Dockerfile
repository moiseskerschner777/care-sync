FROM python:3.12-slim
WORKDIR /python-code-rag
RUN python -m venv .venv
ENV PATH="/python-code-rag/.venv/bin:$PATH"
COPY pyproject.toml .
RUN pip install -e .
COPY app/ app/
COPY mcp_server/ mcp_server/
COPY start.sh .
RUN chmod +x start.sh
CMD ["./start.sh"]
