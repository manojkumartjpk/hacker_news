from pydantic import BaseModel

class VoteBase(BaseModel):
    vote_type: int  # 1 or -1

class VoteCreate(VoteBase):
    pass

class Vote(VoteBase):
    id: int
    user_id: int
    post_id: int

    class Config:
        from_attributes = True