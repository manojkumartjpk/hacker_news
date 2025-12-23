from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from models import Vote
from schemas import VoteCreate
from services.post_service import PostService
from fastapi import HTTPException

class VoteService:
    @staticmethod
    def vote_on_post(db: Session, post_id: int, vote: VoteCreate, user_id: int) -> Vote:
        # Check if user already voted on this post
        existing_vote = db.query(Vote).filter(
            Vote.user_id == user_id,
            Vote.post_id == post_id
        ).first()

        if existing_vote:
            # Update existing vote
            existing_vote.vote_type = vote.vote_type
            db.commit()
            db.refresh(existing_vote)
            vote_obj = existing_vote
        else:
            # Create new vote
            db_vote = Vote(
                user_id=user_id,
                post_id=post_id,
                vote_type=vote.vote_type
            )
            db.add(db_vote)
            try:
                db.commit()
                db.refresh(db_vote)
                vote_obj = db_vote
            except IntegrityError:
                db.rollback()
                raise HTTPException(status_code=400, detail="Vote creation failed")

        # Update post score after voting
        PostService.update_post_score(db, post_id)

        return vote_obj

    @staticmethod
    def get_user_vote_on_post(db: Session, post_id: int, user_id: int) -> Vote:
        return db.query(Vote).filter(
            Vote.user_id == user_id,
            Vote.post_id == post_id
        ).first()