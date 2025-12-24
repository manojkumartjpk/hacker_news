#!/bin/sh
set -e

USE_DOCKER_TESTS="${USE_DOCKER_TESTS:-1}"
PYTEST_MARK="${PYTEST_MARK:-}"
JEST_ARGS="${JEST_ARGS:-}"
COVERAGE="${COVERAGE:-0}"
RUN_E2E="${RUN_E2E:-0}"
ONLY_E2E="${ONLY_E2E:-0}"

if [ "$ONLY_E2E" = "1" ]; then
  RUN_E2E=1
fi

if [ "$USE_DOCKER_TESTS" = "1" ]; then
  cleanup() {
    docker compose -f docker-compose.test.yml down -v
  }
  trap cleanup EXIT

  services="postgres redis"
  if [ "$RUN_E2E" = "1" ]; then
    services="$services backend frontend"
  fi
  docker compose -f docker-compose.test.yml up -d $services
  if [ "$ONLY_E2E" != "1" ]; then
    pytest_cmd="pytest"
    if [ -n "$PYTEST_MARK" ]; then
      pytest_cmd="$pytest_cmd -m \"$PYTEST_MARK\""
    fi
    if [ "$COVERAGE" = "1" ]; then
      pytest_cmd="$pytest_cmd --cov=. --cov-config=.coveragerc --cov-report=term-missing --cov-report=xml:coverage/backend-coverage.xml"
    fi
    docker compose -f docker-compose.test.yml run --rm backend-tests sh -c "$pytest_cmd"

    jest_cmd="npm test"
    if [ -n "$JEST_ARGS" ]; then
      jest_cmd="$jest_cmd -- $JEST_ARGS"
    fi
    if [ "$COVERAGE" = "1" ]; then
      jest_cmd="$jest_cmd -- --coverage --watchAll=false --coverageDirectory=coverage/frontend"
    fi
    docker compose -f docker-compose.test.yml run --rm frontend-tests sh -c "$jest_cmd"
  fi

  if [ "$RUN_E2E" = "1" ]; then
    docker compose -f docker-compose.test.yml run --rm e2e-tests
  fi
else
  if [ "$ONLY_E2E" != "1" ]; then
    pytest_cmd="pytest"
    if [ -n "$PYTEST_MARK" ]; then
      pytest_cmd="$pytest_cmd -m \"$PYTEST_MARK\""
    fi
    if [ "$COVERAGE" = "1" ]; then
      pytest_cmd="$pytest_cmd --cov=. --cov-config=.coveragerc --cov-report=term-missing --cov-report=xml:../coverage/backend-coverage.xml"
    fi
    (cd backend && sh -c "$pytest_cmd")

    jest_cmd="npm test"
    if [ -n "$JEST_ARGS" ]; then
      jest_cmd="$jest_cmd -- $JEST_ARGS"
    fi
    if [ "$COVERAGE" = "1" ]; then
      jest_cmd="$jest_cmd -- --coverage --watchAll=false --coverageDirectory=../coverage/frontend"
    fi
    (cd frontend && sh -c "$jest_cmd")
  fi

  if [ "$RUN_E2E" = "1" ]; then
    (cd frontend && E2E_BASE_URL="${E2E_BASE_URL:-http://localhost:3000}" npm run test:e2e)
  fi
fi
