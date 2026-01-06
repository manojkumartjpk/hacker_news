from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from schemas import VoteCreate, VoteStatus, VoteBulkRequest, VoteStatusWithPost
from services import VoteService
from auth.deps import get_current_user
from models import User
from rate_limit import rate_limit

router = APIRouter()

@router.post("/votes/bulk", response_model=list[VoteStatusWithPost])
def get_user_votes_bulk(
    payload: VoteBulkRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    rate_limited: bool = Depends(rate_limit())
):
    """Return the current user's votes for a list of posts."""
    return VoteService.get_user_votes_for_posts(db, current_user.id, payload.post_ids)

@router.post("/{post_id}/vote", response_model=VoteStatus)
def vote_on_post(
    post_id: int,
    vote: VoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    rate_limited: bool = Depends(rate_limit())
):
    """Upvote a post for the authenticated user."""
    if vote.vote_type != 1:
        raise HTTPException(status_code=400, detail="Vote type must be 1 (upvote)")
    VoteService.vote_on_post(db, post_id, vote, current_user.id)
    return {"vote_type": 1}

@router.get("/{post_id}/vote", response_model=VoteStatus)
def get_user_vote_on_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Return the current user's vote on a post."""
    vote = VoteService.get_user_vote_on_post(db, post_id, current_user.id)
    if vote:
        return {"vote_type": 1}
    return {"vote_type": 0}

@router.delete("/{post_id}/vote", response_model=VoteStatus)
def remove_vote_on_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    rate_limited: bool = Depends(rate_limit())
):
    """Remove the current user's vote on a post."""
    VoteService.remove_vote_on_post(db, post_id, current_user.id)
    return {"vote_type": 0}
