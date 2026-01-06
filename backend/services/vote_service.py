from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from models import Vote, Post
from schemas import VoteCreate
from services.post_service import PostService
from fastapi import HTTPException

class VoteService:
    @staticmethod
    def vote_on_post(db: Session, post_id: int, vote: VoteCreate, user_id: int) -> Vote:
        post = db.query(Post).filter(Post.id == post_id).first()
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")

        existing_vote = db.query(Vote).filter(
            Vote.user_id == user_id,
            Vote.post_id == post_id
        ).first()
        if existing_vote:
            return existing_vote
        else:
            db_vote = Vote(
                user_id=user_id,
                post_id=post_id
            )
            db.add(db_vote)
            try:
                db.commit()
                db.refresh(db_vote)
                # Update post points after a new vote.
                PostService.adjust_post_points(db, post_id, 1)
                vote_obj = db_vote
            except IntegrityError:
                db.rollback()
                raise HTTPException(status_code=409, detail="Vote creation failed")

        return vote_obj

    @staticmethod
    def get_user_vote_on_post(db: Session, post_id: int, user_id: int) -> Vote:
        post = db.query(Post).filter(Post.id == post_id).first()
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")

        return db.query(Vote).filter(
            Vote.user_id == user_id,
            Vote.post_id == post_id
        ).order_by(Vote.created_at.desc()).first()

    @staticmethod
    def remove_vote_on_post(db: Session, post_id: int, user_id: int) -> None:
        post = db.query(Post).filter(Post.id == post_id).first()
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")

        existing_vote = db.query(Vote).filter(
            Vote.user_id == user_id,
            Vote.post_id == post_id
        ).first()
        if existing_vote:
            db.delete(existing_vote)
            db.commit()
            PostService.adjust_post_points(db, post_id, -1)

    @staticmethod
    def get_user_votes_for_posts(db: Session, user_id: int, post_ids: list[int]) -> list[dict]:
        if not post_ids:
            return []
        unique_ids = list(dict.fromkeys(post_ids))
        votes = db.query(Vote.post_id).filter(
            Vote.user_id == user_id,
            Vote.post_id.in_(unique_ids)
        ).all()
        vote_map = {post_id: 1 for (post_id,) in votes}
        return [
            {"post_id": post_id, "vote_type": vote_map.get(post_id, 0)}
            for post_id in unique_ids
        ]
