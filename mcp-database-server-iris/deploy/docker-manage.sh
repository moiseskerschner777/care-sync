#!/usr/bin/env bash
set -eo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
COMPOSE_FILE="$PROJECT_DIR/docker-compose.yml"
IMAGE_NAME="iris-mcp-server"
CONTAINER_NAME="iris-mcp-server"

build() {
  echo "==> Building $IMAGE_NAME image..."
  docker build -t "$IMAGE_NAME" -f "$PROJECT_DIR/Dockerfile" "$PROJECT_DIR"
  echo "==> Build complete."
}

start() {
  echo "==> Starting IRIS database and $CONTAINER_NAME..."
  docker compose -f "$COMPOSE_FILE" up -d
  echo "==> Containers started."
}

stop() {
  echo "==> Stopping containers..."
  docker compose -f "$COMPOSE_FILE" down
  echo "==> Containers stopped."
}

logs() {
  docker compose -f "$COMPOSE_FILE" logs -f
}

status() {
  docker compose -f "$COMPOSE_FILE" ps
}

case "${1:-help}" in
  build)  build ;;
  start)  start ;;
  stop)   stop ;;
  logs)   logs ;;
  status) status ;;
  *)
    echo "Usage: $0 {build|start|stop|logs|status}"
    exit 1
    ;;
esac
