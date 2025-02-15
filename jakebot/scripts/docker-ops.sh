#!/bin/bash

# Default to production mode
COMPOSE_FILE="docker-compose.yml"

# Check for development flag
if [ "$2" == "dev" ]; then
    COMPOSE_FILE="docker-compose.yml -f docker-compose.dev.yml"
fi

case "$1" in
  "build")
    docker-compose -f $COMPOSE_FILE build
    ;;
  "up")
    docker-compose -f $COMPOSE_FILE up -d
    ;;
  "down")
    docker-compose -f $COMPOSE_FILE down
    ;;
  "logs")
    docker-compose -f $COMPOSE_FILE logs -f
    ;;
  "restart")
    docker-compose -f $COMPOSE_FILE restart
    ;;
  "clean")
    docker-compose -f $COMPOSE_FILE down -v
    docker system prune -f
    ;;
  "test")
    docker-compose -f $COMPOSE_FILE run --rm api pytest
    ;;
  *)
    echo "Usage: $0 {build|up|down|logs|restart|clean|test} [dev]"
    echo "Add 'dev' for development mode"
    exit 1
    ;;
esac 