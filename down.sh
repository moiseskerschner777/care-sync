#!/bin/bash

set -e

echo "Stopping containers..."
docker compose down --remove-orphans

echo "Removing project volumes..."
docker volume ls -q | grep iris-data | xargs -r docker volume rm

echo "Pruning leftover networks..."
docker network prune -f


