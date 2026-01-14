from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from services.comment_ancestor_service import CommentAncestorService


router = APIRouter()


@router.post("/ancestors/backfill/{post_id}")
def backfill_comment_ancestors(
    post_id: int,
    db: Session = Depends(get_db),
):
    return CommentAncestorService.backfill_for_post(db, post_id)
