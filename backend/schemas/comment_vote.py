from pydantic import BaseModel


class CommentVoteCreate(BaseModel):
    vote_type: int = 1
