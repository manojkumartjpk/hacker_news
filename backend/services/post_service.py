from datetime import date, datetime, time, timezone
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from models import Post, User, Comment
from schemas import PostCreate
from fastapi import HTTPException
from cache import redis_get, redis_setex, redis_incr
import json

class PostService:
    FEED_CACHE_TTL_SECONDS = 300

    @staticmethod
    def _feed_cache_key(
        sort: str,
        skip: int,
        limit: int,
        post_type: str | None,
        day_key: str | None,
        version: int
    ) -> str:
        type_key = post_type or "all"
        day_value = day_key or "all"
        return f"feed:{sort}:{type_key}:day:{day_value}:v{version}:skip:{skip}:limit:{limit}"

    @staticmethod
    def _get_feed_cache_version() -> int:
        cached = redis_get("feed:version")
        if cached is None:
            initial = redis_incr("feed:version")
            if initial is None:
                return 1
            return int(initial)
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
    def _serialize_datetime(value):
        return value.isoformat() if hasattr(value, "isoformat") else value

    @staticmethod
    def _rank_expression(db: Session):
        if db.bind and db.bind.dialect.name == "sqlite":
            return Post.points
        age_hours = func.extract("epoch", func.now() - Post.created_at) / 3600.0
        return (Post.points - 1) / func.power(age_hours + 2, 1.8)

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
            "points": db_post.points,
            "comment_count": 0,
            "user_id": db_post.user_id,
            "created_at": PostService._serialize_datetime(db_post.created_at),
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
        return {
            "id": post.id,
            "title": post.title,
            "url": post.url,
            "text": post.text,
            "post_type": post.post_type,
            "points": post.points,
            "comment_count": comment_count or 0,
            "user_id": post.user_id,
            "created_at": PostService._serialize_datetime(post.created_at),
            "username": username
        }

    @staticmethod
    def get_posts(
        db: Session,
        skip: int = 0,
        limit: int = 10,
        sort: str = "new",
        day: date | None = None,
        post_type: str | None = None
    ) -> list[dict]:
        sort_key = sort
        day_filter = None
        if sort_key == "past":
            if day is None:
                latest_query = db.query(func.max(Post.created_at))
                if post_type:
                    latest_query = latest_query.filter(Post.post_type == post_type)
                latest_created_at = latest_query.scalar()
                if latest_created_at is None:
                    return []
                day_filter = latest_created_at.date()
            else:
                day_filter = day
        day_key = day_filter.isoformat() if day_filter else None
        cache_version = PostService._get_feed_cache_version()
        cache_key = PostService._feed_cache_key(sort_key, skip, limit, post_type, day_key, cache_version)
        cached = redis_get(cache_key)
        if cached:
            try:
                cached_posts = json.loads(cached)
                if cached_posts and "points" not in cached_posts[0]:
                    raise ValueError("stale-cache")
                return cached_posts
            except (json.JSONDecodeError, ValueError, TypeError):
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
        if day_filter:
            start = datetime.combine(day_filter, time.min, tzinfo=timezone.utc)
            end = datetime.combine(day_filter, time.max, tzinfo=timezone.utc)
            query = query.filter(Post.created_at.between(start, end))
        if sort_key == "past":
            rank_expr = PostService._rank_expression(db)
            query = query.order_by(desc(rank_expr), desc(Post.created_at))
        else:  # "new"
            query = query.order_by(desc(Post.created_at))

        results = query.offset(skip).limit(limit).all()

        posts_with_username = []
        for post, username, comment_count in results:
            post_dict = {
                "id": post.id,
                "title": post.title,
                "url": post.url,
                "text": post.text,
                "post_type": post.post_type,
                "points": post.points,
                "comment_count": comment_count or 0,
                "user_id": post.user_id,
                "created_at": PostService._serialize_datetime(post.created_at),
                "username": username
            }
            posts_with_username.append(post_dict)

        redis_setex(cache_key, PostService.FEED_CACHE_TTL_SECONDS, json.dumps(posts_with_username))

        return posts_with_username

    @staticmethod
    def adjust_post_points(db: Session, post_id: int, delta: int) -> None:
        if delta == 0:
            return None
        updated = db.query(Post).filter(Post.id == post_id).update(
            {Post.points: Post.points + delta}
        )
        if updated:
            db.commit()
            # Ranking depends on points, so invalidate cached feeds.
            PostService.bump_feed_cache_version()

    @staticmethod
    def search_posts(db: Session, query: str, skip: int = 0, limit: int = 30) -> list[dict]:
        if not query.strip():
            return []

        comment_count_subq = db.query(
            Comment.post_id.label("post_id"),
            func.count(Comment.id).label("comment_count")
        ).group_by(Comment.post_id).subquery()

        search_query = db.query(
            Post,
            User.username,
            comment_count_subq.c.comment_count
        ).join(User).outerjoin(
            comment_count_subq,
            comment_count_subq.c.post_id == Post.id
        )

        if db.bind and db.bind.dialect.name == "sqlite":
            like_term = f"%{query}%"
            search_query = search_query.filter(
                (Post.title.ilike(like_term)) |
                (Post.url.ilike(like_term)) |
                (Post.text.ilike(like_term))
            )
        else:
            search_vector = func.to_tsvector(
                "english",
                func.concat_ws(" ", Post.title, Post.text, Post.url)
            )
            ts_query = func.plainto_tsquery("english", query)
            search_query = search_query.filter(search_vector.op("@@")(ts_query))

        search_query = search_query.order_by(desc(Post.created_at)).offset(skip).limit(limit)

        results = search_query.all()
        posts_with_username = []
        for post, username, comment_count in results:
            posts_with_username.append({
                "id": post.id,
                "title": post.title,
                "url": post.url,
                "text": post.text,
                "post_type": post.post_type,
                "points": post.points,
                "comment_count": comment_count or 0,
                "user_id": post.user_id,
                "created_at": PostService._serialize_datetime(post.created_at),
                "username": username
            })

        return posts_with_username
