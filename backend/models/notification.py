from sqlalchemy import Text, Integer, DateTime, ForeignKey, func, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum
from database import Base

class NotificationType(enum.Enum):
    COMMENT_ON_POST = "comment_on_post"
    REPLY_TO_COMMENT = "reply_to_comment"

class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))  # Recipient
    actor_id: Mapped[int] = mapped_column(ForeignKey("users.id"))  # Who triggered the notification
    type: Mapped[NotificationType] = mapped_column(Enum(NotificationType))
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id"), nullable=True)
    comment_id: Mapped[int] = mapped_column(ForeignKey("comments.id"), nullable=True)
    message: Mapped[str] = mapped_column(Text)
    read: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user: Mapped["User"] = relationship(foreign_keys=[user_id], back_populates="notifications")
    actor: Mapped["User"] = relationship(foreign_keys=[actor_id], back_populates="sent_notifications")
    post: Mapped["Post"] = relationship()
    comment: Mapped["Comment"] = relationship()