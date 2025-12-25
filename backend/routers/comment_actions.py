from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from schemas import CommentUpdate, Comment
from services import CommentService
from auth.deps import get_current_user
from models import User
from rate_limit import rate_limit

router = APIRouter()


@router.put("/{comment_id}", response_model=Comment)
def update_comment(
    comment_id: int,
    comment_update: CommentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    rate_limited: bool = Depends(rate_limit())
):
    """Update a comment owned by the authenticated user."""
    return CommentService.update_comment(db, comment_id, comment_update, current_user.id)


@router.delete("/{comment_id}")
def delete_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    rate_limited: bool = Depends(rate_limit())
):
    """Delete a comment owned by the authenticated user."""
    CommentService.delete_comment(db, comment_id, current_user.id)
    return {"message": "Comment deleted successfully"}
