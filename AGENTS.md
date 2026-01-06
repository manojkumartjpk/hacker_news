# AGENTS.md

This repository is a Hacker News clone with a Next.js frontend and a FastAPI backend.

## Stack at a glance
- Frontend: Next.js (React), Tailwind CSS
- Backend: FastAPI (Python 3.11) with SQLAlchemy 2.0
- Data: PostgreSQL (system of record), Redis (cache/rate limiting)
- Infra: Caddy, Docker Compose
- CI/CD: GitHub Actions (CD on main)

## Repo layout
- `frontend/`: Next.js app (React components, pages, client API)
- `backend/`: FastAPI app (routers, services, models, schemas)
- `docker-compose*.yml`: local/test/prod compose stacks
- `Caddyfile`: reverse proxy config
- `scripts/`: helper scripts (tests, etc.)

## Development
- Full stack (dev, no Caddy):
  - `docker compose -f docker-compose.dev.yml up --build`
- Full stack (includes Caddy):
  - `docker compose up --build`
- Local frontend:
  - `cd frontend && npm install && npm run dev`
- Local backend:
  - `cd backend && pip install -r requirements.txt`
  - `uvicorn main:app --reload`

## Environment notes
- Backend (local): copy `backend/.env.example` to `backend/.env`
- Required: `SECRET_KEY`
- Optional: `ENVIRONMENT`, `COOKIE_SECURE`
- Frontend: `NEXT_PUBLIC_API_URL` (defaults to `http://localhost:8000`)

## Tests
- Run all (dockerized): `./scripts/run-tests.sh`
- Run all (local): `USE_DOCKER_TESTS=0 ./scripts/run-tests.sh`
- Backend unit: `PYTEST_MARK=unit ./scripts/run-tests.sh`
- Backend integration: `PYTEST_MARK=integration ./scripts/run-tests.sh`
- Frontend: `USE_DOCKER_TESTS=0 (cd frontend && npm test)`

## Project conventions
- Prefer SQLAlchemy for DB access and keep business logic in `backend/services`.
- Keep routers thin; validation in schemas.
- Use Tailwind CSS for styling; avoid duplicating utility classes and limit inline styles.
