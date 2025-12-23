from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

# Import database and create tables on startup
from database import engine, Base

app = FastAPI(
    title="Hacker News Clone API",
    description="A REST API for a Hacker News-style application",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for Docker environment
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
    notifications_router,
    comments_feed_router
)

# Include routers with prefixes
app.include_router(auth_router, prefix="/auth", tags=["authentication"])
app.include_router(posts_router, prefix="/posts", tags=["posts"])
app.include_router(votes_router, prefix="/posts", tags=["votes"])
app.include_router(comments_router, prefix="/posts", tags=["comments"])
app.include_router(comments_feed_router, prefix="/comments", tags=["comments"])
app.include_router(notifications_router, prefix="/notifications", tags=["notifications"])

# Create tables on startup
@app.on_event("startup")
def create_tables():
    Base.metadata.create_all(bind=engine)

@app.get("/")
def read_root():
    return {"message": "Hacker News Clone API", "version": "1.0.0"}
