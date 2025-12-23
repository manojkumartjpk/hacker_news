from sqlalchemy.orm import Session
from models import Comment, Notification, NotificationType, User, Post
from schemas import CommentCreate, CommentUpdate
from fastapi import HTTPException

class CommentService:
    @staticmethod
    def create_comment(db: Session, comment: CommentCreate, post_id: int, user_id: int) -> dict:
        db_comment = Comment(
            text=comment.text,
            user_id=user_id,
            post_id=post_id,
            parent_id=comment.parent_id
        )
        db.add(db_comment)
        db.commit()
        db.refresh(db_comment)

        # Create notification
        CommentService._create_notification_for_comment(db, db_comment)

        # Get username
        user = db.query(User).filter(User.id == user_id).first()
        
        return {
            "id": db_comment.id,
            "text": db_comment.text,
            "user_id": db_comment.user_id,
            "post_id": db_comment.post_id,
            "parent_id": db_comment.parent_id,
            "created_at": db_comment.created_at,
            "username": user.username
        }

    @staticmethod
    def get_comment(db: Session, comment_id: int) -> Comment:
        comment = db.query(Comment).filter(Comment.id == comment_id).first()
        if not comment:
            raise HTTPException(status_code=404, detail="Comment not found")
        return comment

    @staticmethod
    def get_comments_for_post(db: Session, post_id: int) -> list[dict]:
        # Get all comments for the post with usernames
        results = db.query(Comment, User.username).join(User).filter(
            Comment.post_id == post_id
        ).order_by(Comment.created_at).all()
        
        # Convert to dicts
        comments_dict = {}
        for comment, username in results:
            comment_dict = {
                "id": comment.id,
                "text": comment.text,
                "user_id": comment.user_id,
                "post_id": comment.post_id,
                "parent_id": comment.parent_id,
                "created_at": comment.created_at,
                "username": username,
                "replies": []
            }
            comments_dict[comment.id] = comment_dict
        
        # Build threaded structure
        top_level_comments = []
        for comment_id, comment in comments_dict.items():
            if comment["parent_id"] is None:
                top_level_comments.append(comment)
            else:
                parent = comments_dict.get(comment["parent_id"])
                if parent:
                    parent["replies"].append(comment)
        
        return top_level_comments

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
            "created_at": comment.created_at,
            "username": user.username
        }

    @staticmethod
    def delete_comment(db: Session, comment_id: int, user_id: int):
        comment = CommentService.get_comment(db, comment_id)
        if comment.user_id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this comment")

        db.delete(comment)
        db.commit()

    @staticmethod
    def _create_notification_for_comment(db: Session, comment: Comment):
        # Get the post and user info
        post = db.query(Post).filter(Post.id == comment.post_id).first()
        actor = db.query(User).filter(User.id == comment.user_id).first()
        
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