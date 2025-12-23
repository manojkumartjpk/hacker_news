from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from schemas import Notification
from services import NotificationService
from routers.auth import get_current_user
from models import User
from rate_limit import rate_limit

router = APIRouter()

@router.get("/", response_model=List[Notification])
def get_notifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    rate_limited: bool = Depends(rate_limit(limit=10, window=60))
):
    return NotificationService.get_user_notifications(db, current_user.id, skip=skip, limit=limit)

@router.put("/{notification_id}/read")
def mark_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    rate_limited: bool = Depends(rate_limit(limit=10, window=60))
):
    NotificationService.mark_notification_as_read(db, notification_id, current_user.id)
    return {"message": "Notification marked as read"}

@router.get("/unread/count")
def get_unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    rate_limited: bool = Depends(rate_limit(limit=60, window=60))
):
    count = NotificationService.get_unread_count(db, current_user.id)
    return {"unread_count": count}
