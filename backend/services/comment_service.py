from sqlalchemy.orm import Session
from models import Comment, Notification, NotificationType, User, Post, CommentVote
from sqlalchemy import func
from schemas import CommentCreate, CommentUpdate
from services.post_service import PostService
from fastapi import HTTPException

class CommentService:
    @staticmethod
    def _build_thread_with_scores(rows: list[tuple[Comment, str, int | None]]) -> list[dict]:
        comments_dict: dict[int, dict] = {}
        for comment, username, score in rows:
            comments_dict[comment.id] = {
                "id": comment.id,
                "text": comment.text,
                "user_id": comment.user_id,
                "post_id": comment.post_id,
                "parent_id": comment.parent_id,
                "created_at": comment.created_at,
                "username": username,
                "score": score or 0,
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

        def aggregate_scores(node: dict) -> int:
            total = node["score"]
            for reply in node["replies"]:
                total += aggregate_scores(reply)
            node["score"] = total
            return total

        def sort_replies(node: dict) -> None:
            node["replies"].sort(
                key=lambda item: (item["score"], item["created_at"]),
                reverse=True
            )
            for reply in node["replies"]:
                sort_replies(reply)

        for comment in top_level_comments:
            aggregate_scores(comment)

        top_level_comments.sort(
            key=lambda item: (item["score"], item["created_at"]),
            reverse=True
        )
        for comment in top_level_comments:
            sort_replies(comment)

        return top_level_comments

    @staticmethod
    def _find_comment_score(comments: list[dict], comment_id: int) -> int | None:
        for comment in comments:
            if comment["id"] == comment_id:
                return comment["score"]
            if comment.get("replies"):
                nested_score = CommentService._find_comment_score(comment["replies"], comment_id)
                if nested_score is not None:
                    return nested_score
        return None

    @staticmethod
    def _get_total_score_for_comment(db: Session, comment_id: int, post_id: int) -> int:
        comment_score_subq = db.query(
            CommentVote.comment_id.label("comment_id"),
            func.count(CommentVote.id).label("score")
        ).group_by(CommentVote.comment_id).subquery()

        results = db.query(
            Comment,
            User.username,
            comment_score_subq.c.score
        ).join(User).outerjoin(
            comment_score_subq,
            comment_score_subq.c.comment_id == Comment.id
        ).filter(
            Comment.post_id == post_id
        ).all()

        thread = CommentService._build_thread_with_scores(results)
        return CommentService._find_comment_score(thread, comment_id) or 0

    @staticmethod
    def create_comment(db: Session, comment: CommentCreate, post_id: int, user_id: int) -> dict:
        if not comment.text or not comment.text.strip():
            raise HTTPException(status_code=400, detail="Comment text is required")

        post = db.query(Post).filter(Post.id == post_id).first()
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")

        if comment.parent_id is not None:
            parent_comment = db.query(Comment).filter(Comment.id == comment.parent_id).first()
            if not parent_comment:
                raise HTTPException(status_code=404, detail="Parent comment not found")
            if parent_comment.post_id != post_id:
                raise HTTPException(status_code=400, detail="Parent comment does not belong to this post")

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
        PostService.bump_feed_cache_version()

        # Get username
        user = db.query(User).filter(User.id == user_id).first()
        
        return {
            "id": db_comment.id,
            "text": db_comment.text,
            "user_id": db_comment.user_id,
            "post_id": db_comment.post_id,
            "parent_id": db_comment.parent_id,
            "created_at": db_comment.created_at,
            "username": user.username,
            "score": 0
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

        # Precompute scores per comment so we can join them in one query.
        comment_score_subq = db.query(
            CommentVote.comment_id.label("comment_id"),
            func.count(CommentVote.id).label("score")
        ).group_by(CommentVote.comment_id).subquery()

        results = db.query(
            Comment,
            User.username,
            comment_score_subq.c.score
        ).join(User).outerjoin(
            comment_score_subq,
            comment_score_subq.c.comment_id == Comment.id
        ).filter(
            Comment.post_id == post_id
        ).order_by(Comment.created_at).all()

        return CommentService._build_thread_with_scores(results)

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
                "created_at": comment.created_at,
                "username": username,
                "post_title": post_title,
                "score": 0
            })

        return recent_comments

    @staticmethod
    def get_comment_detail(db: Session, comment_id: int) -> dict:
        comment_score_subq = db.query(
            CommentVote.comment_id.label("comment_id"),
            func.count(CommentVote.id).label("score")
        ).group_by(CommentVote.comment_id).subquery()

        result = db.query(
            Comment,
            User.username,
            Post.title,
            comment_score_subq.c.score
        ).select_from(Comment).join(
            User, Comment.user_id == User.id
        ).join(
            Post, Comment.post_id == Post.id
        ).outerjoin(
            comment_score_subq,
            comment_score_subq.c.comment_id == Comment.id
        ).filter(
            Comment.id == comment_id
        ).first()

        if not result:
            raise HTTPException(status_code=404, detail="Comment not found")

        comment, username, post_title, score = result
        total_score = CommentService._get_total_score_for_comment(db, comment_id, comment.post_id)
        return {
            "id": comment.id,
            "text": comment.text,
            "user_id": comment.user_id,
            "post_id": comment.post_id,
            "parent_id": comment.parent_id,
            "created_at": comment.created_at,
            "username": username,
            "post_title": post_title,
            "score": total_score
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
        total_score = CommentService._get_total_score_for_comment(db, comment_id, comment.post_id)
        
        return {
            "id": comment.id,
            "text": comment.text,
            "user_id": comment.user_id,
            "post_id": comment.post_id,
            "parent_id": comment.parent_id,
            "created_at": comment.created_at,
            "username": user.username,
            "score": total_score
        }

    @staticmethod
    def delete_comment(db: Session, comment_id: int, user_id: int):
        comment = CommentService.get_comment(db, comment_id)
        if comment.user_id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this comment")

        # Remove notifications tied to this comment tree to satisfy FK constraints.
        comment_ids = {comment.id}
        frontier = [comment.id]
        while frontier:
            child_ids = db.query(Comment.id).filter(Comment.parent_id.in_(frontier)).all()
            frontier = [row[0] for row in child_ids if row[0] not in comment_ids]
            comment_ids.update(frontier)

        if comment_ids:
            db.query(Notification).filter(Notification.comment_id.in_(comment_ids)).delete(
                synchronize_session=False
            )

        db.delete(comment)
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
