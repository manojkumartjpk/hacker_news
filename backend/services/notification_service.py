from sqlalchemy.orm import Session
from models import Notification, User
from fastapi import HTTPException

class NotificationService:
    @staticmethod
    def get_user_notifications(db: Session, user_id: int, skip: int = 0, limit: int = 20) -> list[dict]:
        results = db.query(Notification, User.username).join(
            User, Notification.actor_id == User.id
        ).filter(
            Notification.user_id == user_id
        ).order_by(Notification.created_at.desc()).offset(skip).limit(limit).all()
        
        notifications = []
        for notification, actor_username in results:
            notifications.append({
                "id": notification.id,
                "user_id": notification.user_id,
                "actor_id": notification.actor_id,
                "type": notification.type,
                "post_id": notification.post_id,
                "comment_id": notification.comment_id,
                "message": notification.message,
                "read": notification.read,
                "created_at": notification.created_at,
                "actor_username": actor_username
            })
        
        return notifications

    @staticmethod
    def mark_notification_as_read(db: Session, notification_id: int, user_id: int):
        notification = db.query(Notification).filter(
            Notification.id == notification_id,
            Notification.user_id == user_id
        ).first()

        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")

        notification.read = True
        db.commit()

    @staticmethod
    def get_unread_count(db: Session, user_id: int) -> int:
        return db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.read == False
        ).count()