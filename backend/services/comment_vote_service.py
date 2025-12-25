from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from models import CommentVote, Comment
from schemas import CommentVoteCreate
from fastapi import HTTPException


class CommentVoteService:
    @staticmethod
    def vote_on_comment(db: Session, comment_id: int, vote: CommentVoteCreate, user_id: int) -> CommentVote:
        comment = db.query(Comment).filter(Comment.id == comment_id).first()
        if not comment:
            raise HTTPException(status_code=404, detail="Comment not found")

        existing_vote = db.query(CommentVote).filter(
            CommentVote.user_id == user_id,
            CommentVote.comment_id == comment_id
        ).first()
        if existing_vote:
            if existing_vote.vote_type == vote.vote_type:
                return existing_vote
            existing_vote.vote_type = vote.vote_type
            db.commit()
            db.refresh(existing_vote)
            return existing_vote

        db_vote = CommentVote(
            user_id=user_id,
            comment_id=comment_id,
            vote_type=vote.vote_type
        )
        db.add(db_vote)
        try:
            db.commit()
            db.refresh(db_vote)
            return db_vote
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=409, detail="Vote creation failed")

    @staticmethod
    def get_comment_score(db: Session, comment_id: int) -> int:
        score = db.query(func.coalesce(func.sum(CommentVote.vote_type), 0)).filter(
            CommentVote.comment_id == comment_id
        ).scalar()
        return int(score or 0)
