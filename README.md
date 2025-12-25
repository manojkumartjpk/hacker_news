# Hacker News Clone

A full-stack Hacker News clone built with Next.js (frontend), FastAPI (backend), PostgreSQL, and Redis.

## Features

- User registration and authentication (JWT)
- Post submission (URL or text posts)
- Upvoting/downvoting posts
- Comment voting
- Threaded comments
- Notifications for comments and replies
- Rate limiting
- Feed filters (story/ask/show/job) and sorting (new/top/best)
- Post search
- Recent comments feed
- Responsive UI

## Tech Stack

### Backend
- **Language**: Python 3.11
- **Framework**: FastAPI
- **ORM**: SQLAlchemy 2.0
- **Database**: PostgreSQL
- **Cache**: Redis
- **Auth**: JWT tokens
- **Password Hashing**: bcrypt

### Frontend
- **Framework**: Next.js 15
- **HTTP Client**: Axios
- **State Management**: React hooks

## Architecture

- **PostgreSQL**: System of record for users, posts, comments, votes, notifications
- **Redis**: Caching for feed data, vote scores, rate limiting
- **REST API**: Clean separation between routers, services, models, and schemas

## Caching and Rate Limiting

- **Feed cache**: Redis caches feed responses for 5 minutes (TTL). Cache is invalidated on new posts and new comments via a feed version bump.
- **Score cache**: Post scores are cached in Redis for 5 minutes (TTL).
- **Rate limits**: Authenticated requests are limited to 120 requests/minute per user. Unauthenticated requests are limited to 20 requests/minute per IP. Limits apply to endpoints using the rate limit dependency.
- **Logout revocation**: Token revocation is stored in Redis. If Redis is disabled or unavailable, logout will not invalidate existing tokens.

## Setup

1. Ensure Docker and Docker Compose are installed.

2. Clone or navigate to the project directory.

3. Export `SECRET_KEY` (for CI, set this as a repository secret and pass it as an env var).

4. Run the following command to start all services (includes Caddy):

   ```bash
   docker-compose up --build
   ```

5. Access the application:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - Database: localhost:5432 (PostgreSQL)
   - Cache: localhost:6379 (Redis)

### Local run without Caddy (recommended)
Start the stack without the reverse proxy:

```bash
docker compose -f docker-compose.dev.yml up --build
```

### Environment variables
- Backend (Docker): `backend/.env` uses container hostnames. `SECRET_KEY` must be set via your environment or repository secrets.
- Backend (local dev): copy `backend/.env.example` to `backend/.env` and set `SECRET_KEY`.
- Frontend: `NEXT_PUBLIC_API_URL` (defaults to `http://localhost:8000`).

## Development

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Backend
```bash
cd backend
pip install -r requirements.txt
export POSTGRES_URL=postgresql://user:password@localhost:5432/hackernews
export REDIS_URL=redis://localhost:6379
uvicorn main:app --reload
```

## Tests (Dockerized by default)

Set `SECRET_KEY` before running tests:

```bash
export SECRET_KEY=your-secret
```

Run all tests in Docker (backend + frontend):

```bash
./scripts/run-tests.sh
```

Skip Docker locally (runs tests directly on your machine):

```bash
USE_DOCKER_TESTS=0 ./scripts/run-tests.sh
```

### Backend unit tests
```bash
PYTEST_MARK=unit ./scripts/run-tests.sh
```

### Backend integration tests (e2e flows)
```bash
PYTEST_MARK=integration ./scripts/run-tests.sh
```

### Frontend tests
```bash
USE_DOCKER_TESTS=0 (cd frontend && npm test)
```

### Browser e2e tests (frontend + backend)
Dockerized:
```bash
RUN_E2E=1 ./scripts/run-tests.sh
```

Dockerized (only e2e):
```bash
ONLY_E2E=1 ./scripts/run-tests.sh
```

Local (requires running frontend + backend separately):
```bash
USE_DOCKER_TESTS=0 RUN_E2E=1 E2E_BASE_URL=http://localhost:3000 ./scripts/run-tests.sh
```

If your API is not on localhost, set `E2E_API_BASE_URL` (defaults to `http://localhost:8000`).

If running locally for the first time, install Playwright browsers:
```bash
cd frontend
npx playwright install
```

### Coverage (backend + frontend)
```bash
COVERAGE=1 ./scripts/run-tests.sh
```

Notes:
- Coverage output is printed to the console when running in Docker.
- To generate host-side coverage artifacts (XML/HTML), run with `USE_DOCKER_TESTS=0`.

## API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login user
- `POST /auth/logout` - Revoke the current token
- `GET /auth/username-available` - Check username availability
- `GET /auth/me` - Current user profile
- Logout revokes the access token and the client clears the JWT cookie.
  - Cookie auth requires `X-CSRF-Token` for POST/PUT/PATCH/DELETE.

### Posts
- `GET /posts/` - Get posts feed (with pagination and sorting)
- `POST /posts/` - Create new post
- `GET /posts/search` - Search posts
- `GET /posts/{post_id}` - Get single post
- `PUT /posts/{post_id}` - Update post
- `DELETE /posts/{post_id}` - Delete post
- `POST /posts/{post_id}/vote` - Vote on post
- `GET /posts/{post_id}/vote` - Get current user's vote

### Comments
- `GET /posts/{post_id}/comments` - Get comments for post
- `POST /posts/{post_id}/comments` - Create comment
- `PUT /posts/{comment_id}` - Update comment
- `DELETE /posts/{comment_id}` - Delete comment
- `GET /comments/recent` - Recent comments feed
- `POST /comments/{comment_id}/vote` - Vote on comment

### Notifications
- `GET /notifications/` - Get user notifications
- `PUT /notifications/{notification_id}/read` - Mark notification as read
- `GET /notifications/unread/count` - Get unread count

## Database Schema

The application uses the following main entities:
- **Users**: Authentication and profile data
- **Posts**: Stories submitted by users
- **Comments**: Threaded discussions on posts
- **Votes**: User votes on posts
- **CommentVotes**: User votes on comments
- **Notifications**: User notifications for interactions

## AI Assistance
- ChatGPT/Codex:
   - Frontend component scaffolding
   - Since i am new to React, help with hooks and state management
   - Backend API route scaffolding
   - Unit and e2e test creation
   - Documentation drafting
   - Code review and refactoring suggestions
