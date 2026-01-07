from pydantic import BaseModel


class Message(BaseModel):
    message: str


class Availability(BaseModel):
    available: bool


class UnreadCount(BaseModel):
    unread_count: int


class QueuedWriteResponse(BaseModel):
    status: str = "queued"
    request_id: str


class QueuedVoteResponse(QueuedWriteResponse):
    vote_type: int
