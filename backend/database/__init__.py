from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
import os

# Database URL from environment
POSTGRES_URL = os.getenv("POSTGRES_URL", "postgresql://user:password@postgres:5432/hackernews")

# SQLAlchemy 2.0 setup
class Base(DeclarativeBase):
    pass

engine = create_engine(POSTGRES_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Import all models to ensure they are registered with SQLAlchemy
from models import User, Post, Comment, Vote, Notification

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()