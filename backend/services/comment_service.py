from sqlalchemy.orm import Session
from sqlalchemy import desc
from models import Comment, NotificationType, User, Post
from schemas import CommentCreate, CommentUpdate
from services.post_service import PostService
from fastapi import HTTPException

class CommentService:
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

        db_comment = Comment(
            text=comment.text,
            user_id=user_id,
            post_id=post_id,
            parent_id=comment.parent_id,
            root_id=root_id,
        )
        db.add(db_comment)
        db.commit()
        db.refresh(db_comment)
        if comment.parent_id is None:
            db_comment.root_id = db_comment.id
            db.commit()
            db.refresh(db_comment)

        # Create notification
        CommentService._create_notification_for_comment(db, db_comment)
        PostService.bump_feed_cache_version()

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

        results = db.query(
            Comment,
            User.username
        ).filter(
            Comment.post_id == post_id
        ).order_by(desc(Comment.created_at)).all()

        return CommentService._build_thread(results)

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

        comment.is_deleted = True
        comment.text = "[deleted]"
        db.commit()
        PostService.bump_feed_cache_version()

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
