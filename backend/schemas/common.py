from pydantic import BaseModel


class Message(BaseModel):
    message: str


class Availability(BaseModel):
    available: bool


class UnreadCount(BaseModel):
    unread_count: int
