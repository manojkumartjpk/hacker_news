from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from schemas import PostCreate, Post, PostUpdate
from services import PostService
from routers.auth import get_current_user
from models import User
from rate_limit import rate_limit

router = APIRouter()

@router.post("/", response_model=Post)
def create_post(
    post: PostCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    rate_limited: bool = Depends(rate_limit(limit=10, window=60))  # 10 posts per minute
):
    return PostService.create_post(db, post, current_user.id)

@router.get("/", response_model=List[Post])
def get_posts(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    sort: str = Query("new", regex="^(new|top|best)$"),
    post_type: str | None = Query(None, regex="^(story|ask|show|job)$"),
    db: Session = Depends(get_db)
):
    posts = PostService.get_posts(db, skip=skip, limit=limit, sort=sort, post_type=post_type)
    return posts

@router.get("/{post_id}", response_model=Post)
def get_post(post_id: int, db: Session = Depends(get_db)):
    return PostService.get_post(db, post_id)

@router.put("/{post_id}", response_model=Post)
def update_post(
    post_id: int,
    post_update: PostUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return PostService.update_post(db, post_id, post_update, current_user.id)

@router.delete("/{post_id}")
def delete_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    PostService.delete_post(db, post_id, current_user.id)
    return {"message": "Post deleted successfully"}
