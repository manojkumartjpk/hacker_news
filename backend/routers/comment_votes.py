from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from schemas import CommentVoteCreate, CommentVote
from services import CommentVoteService
from auth.deps import get_current_user
from models import User
from rate_limit import rate_limit

router = APIRouter()


@router.post("/{comment_id}/vote", response_model=CommentVote)
def vote_on_comment(
    comment_id: int,
    vote: CommentVoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    rate_limited: bool = Depends(rate_limit(limit=120, window=60))
):
    """Upvote or downvote a comment for the authenticated user."""
    if vote.vote_type not in [1, -1]:
        raise HTTPException(status_code=400, detail="Vote type must be 1 (upvote) or -1 (downvote)")
    return CommentVoteService.vote_on_comment(db, comment_id, vote, current_user.id)
