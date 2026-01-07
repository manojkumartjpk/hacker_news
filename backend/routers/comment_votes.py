from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session
from database import get_db
from schemas import CommentVoteCreate, CommentVoteBulkRequest, CommentVoteStatusWithComment, VoteStatus, QueuedVoteResponse
from services import CommentVoteService
from services.queue_service import queue_writes_enabled
from auth.deps import get_current_user
from models import User
from rate_limit import rate_limit

router = APIRouter()


@router.post("/votes/bulk", response_model=list[CommentVoteStatusWithComment])
def get_user_votes_bulk(
    payload: CommentVoteBulkRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    rate_limited: bool = Depends(rate_limit())
):
    """Return the current user's votes for a list of comments."""
    return CommentVoteService.get_user_votes_for_comments(db, current_user.id, payload.comment_ids)


@router.post("/{comment_id}/vote", response_model=VoteStatus | QueuedVoteResponse)
def vote_on_comment(
    comment_id: int,
    vote: CommentVoteCreate,
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    rate_limited: bool = Depends(rate_limit()),
):
    """Upvote a comment for the authenticated user."""
    if vote.vote_type != 1:
        raise HTTPException(status_code=400, detail="Vote type must be 1 (upvote)")
    result = CommentVoteService.vote_on_comment(db, comment_id, vote, current_user.id)
    if queue_writes_enabled():
        response.status_code = status.HTTP_202_ACCEPTED
        return {"status": "queued", "request_id": result, "vote_type": 1}
    response.status_code = status.HTTP_200_OK
    return {"vote_type": 1}


@router.get("/{comment_id}/vote", response_model=VoteStatus)
def get_user_vote_on_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Return the current user's vote on a comment."""
    vote = CommentVoteService.get_user_vote_on_comment(db, comment_id, current_user.id)
    if vote:
        return {"vote_type": 1}
    return {"vote_type": 0}


@router.delete("/{comment_id}/vote", response_model=VoteStatus | QueuedVoteResponse)
def remove_vote_on_comment(
    comment_id: int,
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    rate_limited: bool = Depends(rate_limit()),
):
    """Remove the current user's vote on a comment."""
    result = CommentVoteService.remove_vote_on_comment(db, comment_id, current_user.id)
    if queue_writes_enabled():
        response.status_code = status.HTTP_202_ACCEPTED
        return {"status": "queued", "request_id": result, "vote_type": 0}
    response.status_code = status.HTTP_200_OK
    return {"vote_type": 0}
