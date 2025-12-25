from pydantic import BaseModel, ConfigDict, field_validator
from datetime import datetime
from typing import Optional

ALLOWED_POST_TYPES = {"story", "ask", "show", "job"}


def _validate_post_type(value: Optional[str]) -> Optional[str]:
    if value is None:
        return value
    if value not in ALLOWED_POST_TYPES:
        raise ValueError("post_type must be one of: story, ask, show, job")
    return value


class PostBase(BaseModel):
    title: str
    url: Optional[str] = None
    text: Optional[str] = None
    post_type: Optional[str] = "story"

    @field_validator("post_type")
    @classmethod
    def validate_post_type(cls, value: Optional[str]) -> Optional[str]:
        return _validate_post_type(value)

class PostCreate(PostBase):
    post_type: Optional[str] = "story"

class PostUpdate(BaseModel):
    title: Optional[str] = None
    url: Optional[str] = None
    text: Optional[str] = None
    post_type: Optional[str] = None

    @field_validator("post_type")
    @classmethod
    def validate_post_type(cls, value: Optional[str]) -> Optional[str]:
        return _validate_post_type(value)

class Post(PostBase):
    id: int
    score: int
    comment_count: int
    user_id: int
    created_at: datetime
    username: str  # Add username field

    model_config = ConfigDict(from_attributes=True)

class PostWithUser(Post):
    username: str
