from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import redis
from datetime import datetime
import os

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database URLs from environment
POSTGRES_URL = os.getenv("POSTGRES_URL", "postgresql://user:password@postgres:5432/hackernews")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")

# SQLAlchemy setup for Postgres
engine = create_engine(POSTGRES_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Redis setup
redis_client = redis.Redis.from_url(REDIS_URL)

# Models
class Story(Base):
    __tablename__ = "stories"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    url = Column(String)
    score = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

# Create tables on startup
@app.on_event("startup")
def create_tables():
    Base.metadata.create_all(bind=engine)

@app.get("/")
def read_root():
    return {"message": "Hacker News Clone API"}

@app.get("/stories")
def get_stories():
    db = SessionLocal()
    stories = db.query(Story).all()
    db.close()
    return stories

@app.post("/stories")
def create_story(title: str, url: str):
    db = SessionLocal()
    story = Story(title=title, url=url)
    db.add(story)
    db.commit()
    db.refresh(story)
    db.close()
    return story

# TODO: Add more endpoints for comments, users, etc.