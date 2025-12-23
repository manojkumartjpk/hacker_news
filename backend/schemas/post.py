from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class PostBase(BaseModel):
    title: str
    url: Optional[str] = None
    text: Optional[str] = None
    post_type: Optional[str] = "story"

class PostCreate(PostBase):
    post_type: Optional[str] = "story"

class PostUpdate(BaseModel):
    title: Optional[str] = None
    url: Optional[str] = None
    text: Optional[str] = None
    post_type: Optional[str] = None

class Post(PostBase):
    id: int
    score: int
    user_id: int
    created_at: datetime
    username: str  # Add username field

    class Config:
        from_attributes = True

class PostWithUser(Post):
    username: str
