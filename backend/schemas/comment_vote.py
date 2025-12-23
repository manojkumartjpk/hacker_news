from pydantic import BaseModel
from datetime import datetime


class CommentVoteCreate(BaseModel):
    vote_type: int  # 1 for upvote, -1 for downvote


class CommentVote(BaseModel):
    id: int
    user_id: int
    comment_id: int
    vote_type: int
    created_at: datetime

    class Config:
        from_attributes = True
