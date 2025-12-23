# Hacker News Clone

A full-stack Hacker News clone built with Next.js (frontend), FastAPI (backend), PostgreSQL, and Redis.

## Features

- User registration and authentication (JWT)
- Post submission (URL or text posts)
- Upvoting/downvoting posts
- Threaded comments
- Notifications for comments and replies
- Rate limiting
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
