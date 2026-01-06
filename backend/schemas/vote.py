from pydantic import BaseModel

class VoteCreate(BaseModel):
    vote_type: int = 1


class VoteStatus(BaseModel):
    vote_type: int


class VoteBulkRequest(BaseModel):
    post_ids: list[int]


class VoteStatusWithPost(BaseModel):
    post_id: int
    vote_type: int
