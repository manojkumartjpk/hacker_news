from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from models import Post, User, Vote, Comment
from schemas import PostCreate, PostUpdate
from fastapi import HTTPException
from cache import redis_get, redis_setex, redis_incr
import json

class PostService:
    FEED_CACHE_TTL_SECONDS = 300

    @staticmethod
    def _feed_cache_key(sort: str, skip: int, limit: int, post_type: str | None, version: int) -> str:
        type_key = post_type or "all"
        return f"feed:{sort}:{type_key}:v{version}:skip:{skip}:limit:{limit}"

    @staticmethod
    def _get_feed_cache_version() -> int:
        cached = redis_get("feed:version")
        if cached is None:
            return 1
        try:
            return int(cached)
        except ValueError:
            return 1

    @staticmethod
    def bump_feed_cache_version() -> None:
        # Incrementing the version keeps cache invalidation cheap and explicit.
        new_version = redis_incr("feed:version")
        if new_version is None:
            return None

    @staticmethod
    def create_post(db: Session, post: PostCreate, user_id: int) -> dict:
        # Validate that either url or text is provided
        if not post.url and not post.text:
            raise HTTPException(status_code=400, detail="Post must have either a URL or text content")
        allowed_types = {"story", "ask", "show", "job"}
        if post.post_type and post.post_type not in allowed_types:
            raise HTTPException(status_code=400, detail="Invalid post type")

        db_post = Post(
            title=post.title,
            url=post.url,
            text=post.text,
            post_type=post.post_type or "story",
            user_id=user_id
        )
        db.add(db_post)
        db.commit()
        db.refresh(db_post)
        
        # Get username
        user = db.query(User).filter(User.id == user_id).first()

        # Invalidate cached feeds so new submissions show up quickly.
        PostService.bump_feed_cache_version()
        
        return {
            "id": db_post.id,
            "title": db_post.title,
            "url": db_post.url,
            "text": db_post.text,
            "post_type": db_post.post_type,
            "score": db_post.score,
            "comment_count": 0,
            "user_id": db_post.user_id,
            "created_at": db_post.created_at,
            "username": user.username
        }

    @staticmethod
    def get_post(db: Session, post_id: int) -> dict:
        comment_count_subq = db.query(
            Comment.post_id.label("post_id"),
            func.count(Comment.id).label("comment_count")
        ).group_by(Comment.post_id).subquery()

        result = db.query(
            Post,
            User.username,
            comment_count_subq.c.comment_count
        ).join(User).outerjoin(
            comment_count_subq,
            comment_count_subq.c.post_id == Post.id
        ).filter(Post.id == post_id).first()
        if not result:
            raise HTTPException(status_code=404, detail="Post not found")
        
        post, username, comment_count = result
        cached_score = redis_get(f"post:{post_id}:score")
        score = int(cached_score) if cached_score is not None else post.score
        if cached_score is None:
            redis_setex(f"post:{post_id}:score", PostService.FEED_CACHE_TTL_SECONDS, str(post.score))

        return {
            "id": post.id,
            "title": post.title,
            "url": post.url,
            "text": post.text,
            "post_type": post.post_type,
            "score": score,
            "comment_count": comment_count or 0,
            "user_id": post.user_id,
            "created_at": post.created_at,
            "username": username
        }

    @staticmethod
    def get_posts(
        db: Session,
        skip: int = 0,
        limit: int = 10,
        sort: str = "new",
        post_type: str | None = None
    ) -> list[dict]:
        cache_version = PostService._get_feed_cache_version()
        cache_key = PostService._feed_cache_key(sort, skip, limit, post_type, cache_version)
        cached = redis_get(cache_key)
        if cached:
            try:
                return json.loads(cached)
            except json.JSONDecodeError:
                pass

        comment_count_subq = db.query(
            Comment.post_id.label("post_id"),
            func.count(Comment.id).label("comment_count")
        ).group_by(Comment.post_id).subquery()

        query = db.query(
            Post,
            User.username,
            comment_count_subq.c.comment_count
        ).join(User).outerjoin(
            comment_count_subq,
            comment_count_subq.c.post_id == Post.id
        )
        if post_type:
            query = query.filter(Post.post_type == post_type)
        if sort == "top":
            query = query.order_by(desc(Post.score), desc(Post.created_at))
        elif sort == "best":
            # Simple "best" ranking for demo purposes.
            query = query.order_by(desc(Post.score), desc(Post.created_at))
        else:  # "new"
            query = query.order_by(desc(Post.created_at))

        results = query.offset(skip).limit(limit).all()

        posts_with_username = []
        for post, username, comment_count in results:
            cached_score = redis_get(f"post:{post.id}:score")
            score = int(cached_score) if cached_score is not None else post.score
            if cached_score is None:
                redis_setex(
                    f"post:{post.id}:score",
                    PostService.FEED_CACHE_TTL_SECONDS,
                    str(post.score)
                )
            post_dict = {
                "id": post.id,
                "title": post.title,
                "url": post.url,
                "text": post.text,
                "post_type": post.post_type,
                "score": score,
                "comment_count": comment_count or 0,
                "user_id": post.user_id,
                "created_at": post.created_at.isoformat() if hasattr(post.created_at, "isoformat") else post.created_at,
                "username": username
            }
            posts_with_username.append(post_dict)

        redis_setex(cache_key, PostService.FEED_CACHE_TTL_SECONDS, json.dumps(posts_with_username))

        return posts_with_username

    @staticmethod
    def update_post(db: Session, post_id: int, post_update: PostUpdate, user_id: int) -> dict:
        post = db.query(Post).filter(Post.id == post_id).first()
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        if post.user_id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to update this post")

        update_data = post_update.model_dump(exclude_unset=True)
        if "post_type" in update_data and update_data["post_type"] is None:
            update_data.pop("post_type")
        if "post_type" in update_data:
            allowed_types = {"story", "ask", "show", "job"}
            if update_data["post_type"] not in allowed_types:
                raise HTTPException(status_code=400, detail="Invalid post type")
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
            "post_type": post.post_type,
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
            redis_setex(f"post:{post_id}:score", PostService.FEED_CACHE_TTL_SECONDS, str(score))

            # Score changes affect top/best feeds.
            PostService.bump_feed_cache_version()

        return score

    @staticmethod
    def search_posts(db: Session, query: str, skip: int = 0, limit: int = 30) -> list[dict]:
        if not query.strip():
            return []

        comment_count_subq = db.query(
            Comment.post_id.label("post_id"),
            func.count(Comment.id).label("comment_count")
        ).group_by(Comment.post_id).subquery()

        like_term = f"%{query}%"
        search_query = db.query(
            Post,
            User.username,
            comment_count_subq.c.comment_count
        ).join(User).outerjoin(
            comment_count_subq,
            comment_count_subq.c.post_id == Post.id
        ).filter(
            (Post.title.ilike(like_term)) |
            (Post.url.ilike(like_term)) |
            (Post.text.ilike(like_term))
        ).order_by(desc(Post.created_at)).offset(skip).limit(limit)

        results = search_query.all()
        posts_with_username = []
        for post, username, comment_count in results:
            cached_score = redis_get(f"post:{post.id}:score")
            score = int(cached_score) if cached_score is not None else post.score
            if cached_score is None:
                redis_setex(
                    f"post:{post.id}:score",
                    PostService.FEED_CACHE_TTL_SECONDS,
                    str(post.score)
                )
            posts_with_username.append({
                "id": post.id,
                "title": post.title,
                "url": post.url,
                "text": post.text,
                "post_type": post.post_type,
                "score": score,
                "comment_count": comment_count or 0,
                "user_id": post.user_id,
                "created_at": post.created_at.isoformat() if hasattr(post.created_at, "isoformat") else post.created_at,
                "username": username
            })

        return posts_with_username

    @staticmethod
    def get_cached_score(post_id: int) -> int:
        cached_score = redis_get(f"post:{post_id}:score")
        if cached_score is not None:
            return int(cached_score)
        return 0  # Default if not cached
