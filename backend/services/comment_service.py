from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime, timezone
import json
from models import Comment, NotificationType, User, Post, Notification
from schemas import CommentCreate, CommentUpdate
from cache import redis_get, redis_setex, redis_incr
from services.queue_service import enqueue_write, queue_writes_enabled, WriteEventType
from services.comment_ancestor_service import CommentAncestorService
from fastapi import HTTPException

class CommentService:
    COMMENTS_CACHE_TTL_SECONDS = 300

    @staticmethod
    def _reply_rank_score(comment: dict) -> float:
        created_at = comment.get("created_at")
        if isinstance(created_at, datetime):
            created_at_dt = created_at
        else:
            return float(comment.get("points") or 0)
        if created_at_dt.tzinfo is None:
            created_at_dt = created_at_dt.replace(tzinfo=timezone.utc)
        age_hours = max((datetime.now(timezone.utc) - created_at_dt).total_seconds() / 3600.0, 0.0)
        points = float(comment.get("points") or 0)
        return (points - 1) / pow(age_hours + 2, 1.8)

    @staticmethod
    def _build_thread(rows: list[tuple[Comment, str]]) -> list[dict]:
        comments_dict: dict[int, dict] = {}
        for comment, username in rows:
            comments_dict[comment.id] = {
                "id": comment.id,
                "text": comment.text,
                "user_id": comment.user_id,
                "post_id": comment.post_id,
                "parent_id": comment.parent_id,
                "root_id": comment.root_id,
                "is_deleted": comment.is_deleted,
                "points": comment.points,
                "prev_id": None,
                "next_id": None,
                "created_at": comment.created_at,
                "updated_at": comment.updated_at,
                "username": username,
                "replies": []
            }

        top_level_comments: list[dict] = []
        for comment_id, comment in comments_dict.items():
            parent_id = comment["parent_id"]
            if parent_id is None:
                top_level_comments.append(comment)
                continue
            parent = comments_dict.get(parent_id)
            if parent:
                parent["replies"].append(comment)
            else:
                top_level_comments.append(comment)

        def sort_replies(node: dict) -> None:
            node["replies"].sort(
                key=CommentService._reply_rank_score,
                reverse=True,
            )
            for reply in node["replies"]:
                sort_replies(reply)

        top_level_comments.sort(
            key=lambda item: item["created_at"],
            reverse=True,
        )
        for comment in top_level_comments:
            sort_replies(comment)

        CommentService._apply_thread_navigation(top_level_comments)

        return top_level_comments

    @staticmethod
    def _build_thread_from_cte(rows) -> list[dict]:
        comments_dict: dict[int, dict] = {}
        for row in rows:
            data = row._mapping
            comments_dict[data["id"]] = {
                "id": data["id"],
                "text": data["text"],
                "user_id": data["user_id"],
                "post_id": data["post_id"],
                "parent_id": data["parent_id"],
                "root_id": data["root_id"],
                "is_deleted": data["is_deleted"],
                "points": data["points"],
                "prev_id": None,
                "next_id": None,
                "created_at": data["created_at"],
                "updated_at": data["updated_at"],
                "username": data["username"],
                "replies": []
            }

        top_level_comments: list[dict] = []
        for comment_id, comment in comments_dict.items():
            parent_id = comment["parent_id"]
            if parent_id is None:
                top_level_comments.append(comment)
                continue
            parent = comments_dict.get(parent_id)
            if parent:
                parent["replies"].append(comment)
            else:
                top_level_comments.append(comment)

        def sort_replies(node: dict) -> None:
            node["replies"].sort(
                key=lambda item: item["created_at"],
                reverse=True,
            )
            for reply in node["replies"]:
                sort_replies(reply)

        top_level_comments.sort(
            key=lambda item: item["created_at"],
            reverse=True,
        )
        for comment in top_level_comments:
            sort_replies(comment)

        CommentService._apply_thread_navigation(top_level_comments)

        return top_level_comments

    @staticmethod
    def _flatten_thread(top_level_comments: list[dict]) -> list[dict]:
        ordered: list[dict] = []

        def walk(node: dict) -> None:
            ordered.append(node)
            for reply in node["replies"]:
                walk(reply)

        for top_level in top_level_comments:
            walk(top_level)
        return ordered

    @staticmethod
    def _apply_thread_navigation(top_level_comments: list[dict]) -> None:
        ordered = CommentService._flatten_thread(top_level_comments)
        for index, comment in enumerate(ordered):
            comment["prev_id"] = ordered[index - 1]["id"] if index > 0 else None
            comment["next_id"] = ordered[index + 1]["id"] if index + 1 < len(ordered) else None

    @staticmethod
    def _serialize_datetime(value):
        return value.isoformat() if hasattr(value, "isoformat") else value

    @staticmethod
    def _comments_cache_key(post_id: int, version: int) -> str:
        return f"post:{post_id}:comments:v{version}"

    @staticmethod
    def _get_comments_cache_version(post_id: int) -> int:
        cached = redis_get(f"post:{post_id}:comments:v")
        if cached is None:
            initial = redis_incr(f"post:{post_id}:comments:v")
            if initial is None:
                return 1
            return int(initial)
        try:
            return int(cached)
        except ValueError:
            return 1

    @staticmethod
    def bump_comments_cache_version(post_id: int) -> None:
        redis_incr(f"post:{post_id}:comments:v")

    @staticmethod
    def create_comment(db: Session, comment: CommentCreate, post_id: int, user_id: int) -> dict:
        if not comment.text or not comment.text.strip():
            raise HTTPException(status_code=400, detail="Comment text is required")

        post = db.query(Post).filter(Post.id == post_id).first()
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")

        root_id = None
        if comment.parent_id is not None:
            parent_comment = db.query(Comment).filter(Comment.id == comment.parent_id).first()
            if not parent_comment:
                raise HTTPException(status_code=404, detail="Parent comment not found")
            if parent_comment.post_id != post_id:
                raise HTTPException(status_code=400, detail="Parent comment does not belong to this post")
            root_id = parent_comment.root_id or parent_comment.id

        if queue_writes_enabled():
            request_id = enqueue_write(
                WriteEventType.COMMENT_ADD,
                {
                    "user_id": user_id,
                    "post_id": post_id,
                    "parent_id": comment.parent_id,
                    "text": comment.text,
                },
            )
            return {"status": "queued", "request_id": request_id}

        db_comment = Comment(
            text=comment.text,
            user_id=user_id,
            post_id=post_id,
            parent_id=comment.parent_id,
            root_id=root_id,
        )
        db.add(db_comment)
        db.flush()
        if comment.parent_id is None:
            db_comment.root_id = db_comment.id
        CommentAncestorService.create_ancestors_for_comments(db, [db_comment])
        db.commit()
        db.refresh(db_comment)

        # Create notification
        CommentService._create_notification_for_comment(db, db_comment)
        CommentService.bump_comments_cache_version(post_id)

        # Get username
        user = db.query(User).filter(User.id == user_id).first()
        
        return {
            "id": db_comment.id,
            "text": db_comment.text,
            "user_id": db_comment.user_id,
            "post_id": db_comment.post_id,
            "parent_id": db_comment.parent_id,
            "root_id": db_comment.root_id,
            "is_deleted": db_comment.is_deleted,
            "points": db_comment.points,
            "created_at": db_comment.created_at,
            "updated_at": db_comment.updated_at,
            "username": user.username,
        }

    @staticmethod
    def get_comment(db: Session, comment_id: int) -> Comment:
        comment = db.query(Comment).filter(Comment.id == comment_id).first()
        if not comment:
            raise HTTPException(status_code=404, detail="Comment not found")
        return comment

    @staticmethod
    def get_comments_for_post(db: Session, post_id: int) -> list[dict]:
        post = db.query(Post).filter(Post.id == post_id).first()
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")

        cache_version = CommentService._get_comments_cache_version(post_id)
        cache_key = CommentService._comments_cache_key(post_id, cache_version)
        cached = redis_get(cache_key)
        if cached:
            try:
                return json.loads(cached)
            except (json.JSONDecodeError, TypeError):
                pass

        results = db.query(
            Comment,
            User.username
        ).select_from(Comment).join(
            User, Comment.user_id == User.id
        ).filter(
            Comment.post_id == post_id
        ).order_by(desc(Comment.created_at)).all()

        thread = CommentService._build_thread(results)
        redis_setex(
            cache_key,
            CommentService.COMMENTS_CACHE_TTL_SECONDS,
            json.dumps(thread, default=CommentService._serialize_datetime),
        )
        return thread

    @staticmethod
    def get_recent_comments(db: Session, skip: int = 0, limit: int = 30) -> list[dict]:
        results = db.query(
            Comment,
            User.username,
            Post.title
        ).select_from(Comment).join(
            User, Comment.user_id == User.id
        ).join(
            Post, Comment.post_id == Post.id
        ).order_by(Comment.created_at.desc()).offset(skip).limit(limit).all()

        recent_comments = []
        for comment, username, post_title in results:
            recent_comments.append({
                "id": comment.id,
                "text": comment.text,
                "user_id": comment.user_id,
                "post_id": comment.post_id,
                "parent_id": comment.parent_id,
                "root_id": comment.root_id,
                "is_deleted": comment.is_deleted,
                "points": comment.points,
                "created_at": comment.created_at,
                "updated_at": comment.updated_at,
                "username": username,
                "post_title": post_title
            })

        return recent_comments

    @staticmethod
    def get_comment_detail(db: Session, comment_id: int) -> dict:
        result = db.query(
            Comment,
            User.username,
            Post.title
        ).select_from(Comment).join(
            User, Comment.user_id == User.id
        ).join(
            Post, Comment.post_id == Post.id
        ).filter(
            Comment.id == comment_id
        ).first()

        if not result:
            raise HTTPException(status_code=404, detail="Comment not found")

        comment, username, post_title = result
        return {
            "id": comment.id,
            "text": comment.text,
            "user_id": comment.user_id,
            "post_id": comment.post_id,
            "parent_id": comment.parent_id,
            "root_id": comment.root_id,
            "is_deleted": comment.is_deleted,
            "points": comment.points,
            "created_at": comment.created_at,
            "updated_at": comment.updated_at,
            "username": username,
            "post_title": post_title,
        }

    @staticmethod
    def update_comment(db: Session, comment_id: int, comment_update: CommentUpdate, user_id: int) -> dict:
        comment = CommentService.get_comment(db, comment_id)
        if comment.user_id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to update this comment")

        comment.text = comment_update.text
        db.commit()
        db.refresh(comment)
        CommentService.bump_comments_cache_version(comment.post_id)
        
        # Get username
        user = db.query(User).filter(User.id == comment.user_id).first()
        
        return {
            "id": comment.id,
            "text": comment.text,
            "user_id": comment.user_id,
            "post_id": comment.post_id,
            "parent_id": comment.parent_id,
            "root_id": comment.root_id,
            "is_deleted": comment.is_deleted,
            "points": comment.points,
            "created_at": comment.created_at,
            "updated_at": comment.updated_at,
            "username": user.username,
        }

    @staticmethod
    def delete_comment(db: Session, comment_id: int, user_id: int):
        comment = CommentService.get_comment(db, comment_id)
        if comment.user_id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this comment")

        if queue_writes_enabled():
            request_id = enqueue_write(
                WriteEventType.COMMENT_DELETE,
                {"user_id": user_id, "comment_id": comment_id, "post_id": comment.post_id},
            )
            return {"status": "queued", "request_id": request_id}

        comment.is_deleted = True
        comment.text = "[deleted]"
        db.commit()
        CommentService.bump_comments_cache_version(comment.post_id)

    @staticmethod
    def _create_notification_for_comment(db: Session, comment: Comment):
        # Get the post and user info
        post = db.query(Post).filter(Post.id == comment.post_id).first()
        actor = db.query(User).filter(User.id == comment.user_id).first()

        if not post or not actor:
            return
        
        # Notify post author if someone comments on their post
        if comment.user_id != post.user_id:
            notification = Notification(
                user_id=post.user_id,
                actor_id=comment.user_id,
                type=NotificationType.COMMENT_ON_POST,
                post_id=post.id,
                comment_id=comment.id,
                message=f"{actor.username} commented on your post '{post.title}'"
            )
            db.add(notification)

        # Notify parent comment author if it's a reply
        if comment.parent_id:
            parent_comment = db.query(Comment).filter(Comment.id == comment.parent_id).first()
            if not parent_comment:
                return
            if comment.user_id != parent_comment.user_id:
                notification = Notification(
                    user_id=parent_comment.user_id,
                    actor_id=comment.user_id,
                    type=NotificationType.REPLY_TO_COMMENT,
                    post_id=post.id,
                    comment_id=comment.id,
                    message=f"{actor.username} replied to your comment"
                )
                db.add(notification)

        db.commit()
