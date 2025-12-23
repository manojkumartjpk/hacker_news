# Hacker News Clone

A full-stack Hacker News clone built with Next.js (frontend), FastAPI (backend), Postgres, and MongoDB.

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
   - Postgres: localhost:5432
   - MongoDB: localhost:27017

## Development

For development without Docker:

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

## API Endpoints

- GET / : Root message
- GET /stories : Get all stories
- POST /stories : Create a new story (params: title, url)

## TODO

- Add user authentication
- Implement comments
- Add voting system
- Improve UI/UX