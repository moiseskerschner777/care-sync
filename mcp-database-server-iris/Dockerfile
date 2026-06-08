FROM python:3.12-slim
WORKDIR /mcp-database-server-iris
RUN python -m venv .venv
ENV PATH="/mcp-database-server-iris/.venv/bin:$PATH"
COPY pyproject.toml .
COPY src/ src/
RUN pip install .
COPY start.sh .
RUN chmod +x start.sh
CMD ["./start.sh"]
