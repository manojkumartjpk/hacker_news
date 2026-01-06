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
            return existing_vote

        db_vote = CommentVote(
            user_id=user_id,
            comment_id=comment_id
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
        score = db.query(func.count(CommentVote.id)).filter(
            CommentVote.comment_id == comment_id
        ).scalar()
        return int(score or 0)

    @staticmethod
    def get_user_vote_on_comment(db: Session, comment_id: int, user_id: int) -> CommentVote:
        comment = db.query(Comment).filter(Comment.id == comment_id).first()
        if not comment:
            raise HTTPException(status_code=404, detail="Comment not found")

        return db.query(CommentVote).filter(
            CommentVote.user_id == user_id,
            CommentVote.comment_id == comment_id
        ).order_by(CommentVote.created_at.desc()).first()

    @staticmethod
    def remove_vote_on_comment(db: Session, comment_id: int, user_id: int) -> None:
        comment = db.query(Comment).filter(Comment.id == comment_id).first()
        if not comment:
            raise HTTPException(status_code=404, detail="Comment not found")

        existing_vote = db.query(CommentVote).filter(
            CommentVote.user_id == user_id,
            CommentVote.comment_id == comment_id
        ).first()
        if existing_vote:
            db.delete(existing_vote)
            db.commit()

    @staticmethod
    def get_user_votes_for_comments(db: Session, user_id: int, comment_ids: list[int]) -> list[dict]:
        if not comment_ids:
            return []
        unique_ids = list(dict.fromkeys(comment_ids))
        votes = db.query(CommentVote.comment_id).filter(
            CommentVote.user_id == user_id,
            CommentVote.comment_id.in_(unique_ids)
        ).all()
        vote_map = {comment_id: 1 for (comment_id,) in votes}
        return [
            {"comment_id": comment_id, "vote_type": vote_map.get(comment_id, 0)}
            for comment_id in unique_ids
        ]
