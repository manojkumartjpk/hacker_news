from pydantic import BaseModel, ConfigDict, Field, field_validator
from datetime import datetime
from typing import Optional, List

COMMENT_TEXT_MAX_LENGTH = 5000


def _validate_comment_text(value: str) -> str:
    if not value or not value.strip():
        raise ValueError("Comment text is required")
    if len(value) > COMMENT_TEXT_MAX_LENGTH:
        raise ValueError(f"Comment text must be {COMMENT_TEXT_MAX_LENGTH} characters or fewer")
    return value


class CommentBase(BaseModel):
    text: str

    @field_validator("text")
    @classmethod
    def validate_text(cls, value: str) -> str:
        return _validate_comment_text(value)

class CommentCreate(CommentBase):
    parent_id: Optional[int] = None

class CommentUpdate(CommentBase):
    text: str

class Comment(CommentBase):
    id: int
    user_id: int
    post_id: int
    parent_id: Optional[int]
    root_id: Optional[int] = None
    prev_id: Optional[int] = None
    next_id: Optional[int] = None
    is_deleted: bool = False
    created_at: datetime
    updated_at: datetime
    username: str  # Add username field

    model_config = ConfigDict(from_attributes=True)

class CommentWithUser(Comment):
    username: str
    replies: List["CommentWithUser"] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class CommentFeedItem(BaseModel):
    id: int
    text: str
    user_id: int
    post_id: int
    parent_id: Optional[int]
    root_id: Optional[int] = None
    prev_id: Optional[int] = None
    next_id: Optional[int] = None
    is_deleted: bool = False
    created_at: datetime
    updated_at: datetime
    username: str
    post_title: str

    model_config = ConfigDict(from_attributes=True)
