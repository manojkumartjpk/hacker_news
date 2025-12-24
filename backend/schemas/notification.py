from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional
from models import NotificationType

class NotificationBase(BaseModel):
    message: str
    read: bool = False

class Notification(NotificationBase):
    id: int
    user_id: int
    actor_id: int
    type: NotificationType
    post_id: Optional[int]
    comment_id: Optional[int]
    created_at: datetime
    actor_username: str  # Add actor username

    model_config = ConfigDict(from_attributes=True)
