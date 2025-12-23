from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from database import get_db
from services import CommentService
from rate_limit import rate_limit

router = APIRouter()


@router.get("/recent")
def get_recent_comments(
    skip: int = Query(0, ge=0),
    limit: int = Query(30, ge=1, le=100),
    db: Session = Depends(get_db),
    rate_limited: bool = Depends(rate_limit(limit=10, window=60))
):
    """List recent comments across all posts."""
    return CommentService.get_recent_comments(db, skip=skip, limit=limit)
