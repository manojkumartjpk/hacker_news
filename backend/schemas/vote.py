from pydantic import BaseModel, ConfigDict

class VoteBase(BaseModel):
    vote_type: int  # 1 or -1

class VoteCreate(VoteBase):
    pass

class Vote(VoteBase):
    id: int
    user_id: int
    post_id: int

    model_config = ConfigDict(from_attributes=True)


class VoteStatus(BaseModel):
    vote_type: int
