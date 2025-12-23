#!/bin/sh
set -e

USE_DOCKER_TESTS="${USE_DOCKER_TESTS:-1}"

if [ "$USE_DOCKER_TESTS" = "1" ]; then
  cleanup() {
    docker compose -f docker-compose.test.yml down -v
  }
  trap cleanup EXIT

  docker compose -f docker-compose.test.yml up -d postgres redis
  docker compose -f docker-compose.test.yml run --rm backend-tests
  docker compose -f docker-compose.test.yml run --rm frontend-tests
else
  (cd backend && pytest)
  (cd frontend && npm test)
fi
