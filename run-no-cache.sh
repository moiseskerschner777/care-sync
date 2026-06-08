docker compose down -v --remove-orphans
docker network prune -f
docker compose up --build
