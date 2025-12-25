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
- **Styling**: Tailwind CSS
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

## Setup

1. Ensure Docker and Docker Compose are installed.

2. Clone or navigate to the project directory.

3. Run the following command to start all services:

   ```bash
   docker-compose up --build
   ```

4. Access the application:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - Database: localhost:5432 (PostgreSQL)
   - Cache: localhost:6379 (Redis)

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
uvicorn main:app --reload
```

### Docker hot reload
Create containers with live reload enabled (via `docker-compose.override.yml`):

```bash
docker compose up --build
```

## Tests (Dockerized by default)

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

### Posts
- `GET /posts/` - Get posts feed (with pagination and sorting)
- `POST /posts/` - Create new post
- `GET /posts/{post_id}` - Get single post
- `PUT /posts/{post_id}` - Update post
- `DELETE /posts/{post_id}` - Delete post
- `POST /posts/{post_id}/vote` - Vote on post

### Comments
- `GET /posts/{post_id}/comments` - Get comments for post
- `POST /posts/{post_id}/comments` - Create comment
- `PUT /posts/{comment_id}` - Update comment
- `DELETE /posts/{comment_id}` - Delete comment

### Notifications
- `GET /notifications/` - Get user notifications
- `PUT /notifications/{id}/read` - Mark notification as read
- `GET /notifications/unread/count` - Get unread count

## Database Schema

The application uses the following main entities:
- **Users**: Authentication and profile data
- **Posts**: Stories submitted by users
- **Comments**: Threaded discussions on posts
- **Votes**: User votes on posts
- **Notifications**: User notifications for interactions
- Add voting system
- Improve UI/UX
