from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session
from database import get_db
from schemas import CommentUpdate, Comment, CommentFeedItem, QueuedWriteResponse
from services import CommentService
from auth.deps import get_current_user
from models import User
from rate_limit import rate_limit

router = APIRouter()


@router.get("/{comment_id}", response_model=CommentFeedItem)
def get_comment_detail(
    comment_id: int,
    db: Session = Depends(get_db),
    rate_limited: bool = Depends(rate_limit())
):
    """Return a single comment with user and post details."""
    return CommentService.get_comment_detail(db, comment_id)


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


@router.delete("/{comment_id}", response_model=QueuedWriteResponse | None)
def delete_comment(
    comment_id: int,
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    rate_limited: bool = Depends(rate_limit()),
):
    """Delete a comment owned by the authenticated user."""
    result = CommentService.delete_comment(db, comment_id, current_user.id)
    response.status_code = (
        status.HTTP_202_ACCEPTED
        if isinstance(result, dict) and result.get("status") == "queued"
        else status.HTTP_204_NO_CONTENT
    )
    return result
