from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from models import Vote
from schemas import VoteCreate
from services.post_service import PostService
from fastapi import HTTPException

class VoteService:
    @staticmethod
    def vote_on_post(db: Session, post_id: int, vote: VoteCreate, user_id: int) -> Vote:
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
        ).order_by(Vote.created_at.desc()).first()
