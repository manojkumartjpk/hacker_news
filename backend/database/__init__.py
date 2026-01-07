from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker, DeclarativeBase
import os

# Database URL from environment
POSTGRES_URL = os.getenv("POSTGRES_URL", "postgresql://user:password@postgres:5432/hackernews")

# SQLAlchemy 2.0 setup
class Base(DeclarativeBase):
    pass

connect_args = {}
engine_kwargs = {}
if POSTGRES_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
    if ":memory:" in POSTGRES_URL:
        engine_kwargs["poolclass"] = StaticPool

engine = create_engine(POSTGRES_URL, connect_args=connect_args, echo=True, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Import all models to ensure they are registered with SQLAlchemy
from models import User, Post, Comment, Vote, Notification, CommentVote

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
