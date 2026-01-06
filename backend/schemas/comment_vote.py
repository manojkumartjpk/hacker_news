from pydantic import BaseModel


class CommentVoteCreate(BaseModel):
    vote_type: int = 1


class CommentVoteBulkRequest(BaseModel):
    comment_ids: list[int]


class CommentVoteStatusWithComment(BaseModel):
    comment_id: int
    vote_type: int
