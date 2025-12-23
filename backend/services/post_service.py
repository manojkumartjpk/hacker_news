from sqlalchemy.orm import Session
from sqlalchemy import desc
from models import Post, User, Vote
from schemas import PostCreate, PostUpdate
from fastapi import HTTPException
import redis
import os

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")
redis_client = redis.Redis.from_url(REDIS_URL)

class PostService:
    @staticmethod
    def create_post(db: Session, post: PostCreate, user_id: int) -> dict:
        # Validate that either url or text is provided
        if not post.url and not post.text:
            raise HTTPException(status_code=400, detail="Post must have either a URL or text content")

        db_post = Post(
            title=post.title,
            url=post.url,
            text=post.text,
            user_id=user_id
        )
        db.add(db_post)
        db.commit()
        db.refresh(db_post)
        
        # Get username
        user = db.query(User).filter(User.id == user_id).first()
        
        return {
            "id": db_post.id,
            "title": db_post.title,
            "url": db_post.url,
            "text": db_post.text,
            "score": db_post.score,
            "user_id": db_post.user_id,
            "created_at": db_post.created_at,
            "username": user.username
        }

    @staticmethod
    def get_post(db: Session, post_id: int) -> dict:
        result = db.query(Post, User.username).join(User).filter(Post.id == post_id).first()
        if not result:
            raise HTTPException(status_code=404, detail="Post not found")
        
        post, username = result
        return {
            "id": post.id,
            "title": post.title,
            "url": post.url,
            "text": post.text,
            "score": post.score,
            "user_id": post.user_id,
            "created_at": post.created_at,
            "username": username
        }

    @staticmethod
    def get_posts(db: Session, skip: int = 0, limit: int = 10, sort: str = "new") -> list[dict]:
        query = db.query(Post, User.username).join(User)
        if sort == "top":
            # For top posts, we might want to sort by score, but since score is cached,
            # we'll sort by created_at for simplicity in this demo
            query = query.order_by(desc(Post.score), desc(Post.created_at))
        else:  # "new"
            query = query.order_by(desc(Post.created_at))

        results = query.offset(skip).limit(limit).all()
        
        # Convert to dict with username
        posts_with_username = []
        for post, username in results:
            post_dict = {
                "id": post.id,
                "title": post.title,
                "url": post.url,
                "text": post.text,
                "score": post.score,
                "user_id": post.user_id,
                "created_at": post.created_at,
                "username": username
            }
            posts_with_username.append(post_dict)
        
        return posts_with_username

    @staticmethod
    def update_post(db: Session, post_id: int, post_update: PostUpdate, user_id: int) -> dict:
        post = db.query(Post).filter(Post.id == post_id).first()
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        if post.user_id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to update this post")

        update_data = post_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(post, field, value)

        db.commit()
        db.refresh(post)
        
        # Get username
        user = db.query(User).filter(User.id == post.user_id).first()
        
        return {
            "id": post.id,
            "title": post.title,
            "url": post.url,
            "text": post.text,
            "score": post.score,
            "user_id": post.user_id,
            "created_at": post.created_at,
            "username": user.username
        }

    @staticmethod
    def delete_post(db: Session, post_id: int, user_id: int):
        post = db.query(Post).filter(Post.id == post_id).first()
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        if post.user_id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this post")

        db.delete(post)
        db.commit()

    @staticmethod
    def update_post_score(db: Session, post_id: int):
        # Calculate score from votes
        votes = db.query(Vote).filter(Vote.post_id == post_id).all()
        score = sum(vote.vote_type for vote in votes)

        # Update in database
        post = db.query(Post).filter(Post.id == post_id).first()
        if post:
            post.score = score
            db.commit()

            # Cache in Redis
            redis_client.set(f"post:{post_id}:score", score)

        return score

    @staticmethod
    def get_cached_score(post_id: int) -> int:
        cached_score = redis_client.get(f"post:{post_id}:score")
        if cached_score is not None:
            return int(cached_score)
        return 0  # Default if not cached