from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class CommentBase(BaseModel):
    text: str

class CommentCreate(CommentBase):
    parent_id: Optional[int] = None

class CommentUpdate(BaseModel):
    text: str

class Comment(CommentBase):
    id: int
    user_id: int
    post_id: int
    parent_id: Optional[int]
    created_at: datetime
    username: str  # Add username field
    score: int

    class Config:
        from_attributes = True

class CommentWithUser(Comment):
    username: str
    replies: List["CommentWithUser"] = []

    class Config:
        from_attributes = True
