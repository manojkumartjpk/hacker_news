from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from schemas import CommentCreate, CommentWithUser, Comment
from services import CommentService
from auth.deps import get_current_user
from models import User
from rate_limit import rate_limit

router = APIRouter()

@router.post("/{post_id}/comments", response_model=Comment)
def create_comment(
    post_id: int,
    comment: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    rate_limited: bool = Depends(rate_limit(limit=30, window=60))  # 30 comments per minute
):
    """Create a comment on a post for the authenticated user."""
    return CommentService.create_comment(db, comment, post_id, current_user.id)

@router.get("/{post_id}/comments", response_model=List[CommentWithUser])
def get_comments_for_post(
    post_id: int,
    db: Session = Depends(get_db),
    rate_limited: bool = Depends(rate_limit(limit=10, window=60))
):
    """Return the threaded comments for a post."""
    return CommentService.get_comments_for_post(db, post_id)
