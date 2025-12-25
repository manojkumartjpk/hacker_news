from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

# Import database and create tables on startup
from sqlalchemy import text
from database import engine, Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Serialize schema creation across multiple workers to avoid enum race.
    with engine.begin() as conn:
        conn.execute(text("SELECT pg_advisory_lock(2147483647)"))
        try:
            Base.metadata.create_all(bind=conn)
        finally:
            conn.execute(text("SELECT pg_advisory_unlock(2147483647)"))
    yield

app = FastAPI(
    title="Hacker News Clone API",
    description="A REST API for a Hacker News-style application",
    version="1.0.0",
    lifespan=lifespan,
)

allowed_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://frontend:3000"
).split(",")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import routers
from routers import (
    auth_router,
    posts_router,
    votes_router,
    comments_router,
    comment_actions_router,
    notifications_router,
    comments_feed_router,
    comment_votes_router
)

# Include routers with prefixes
app.include_router(auth_router, prefix="/auth", tags=["authentication"])
app.include_router(posts_router, prefix="/posts", tags=["posts"])
app.include_router(votes_router, prefix="/posts", tags=["votes"])
app.include_router(comments_router, prefix="/posts", tags=["comments"])
app.include_router(comments_feed_router, prefix="/comments", tags=["comments"])
app.include_router(comment_actions_router, prefix="/comments", tags=["comments"])
app.include_router(comment_votes_router, prefix="/comments", tags=["comments"])
app.include_router(notifications_router, prefix="/notifications", tags=["notifications"])

@app.get("/")
def read_root():
    return {"message": "Hacker News Clone API", "version": "1.0.0"}
