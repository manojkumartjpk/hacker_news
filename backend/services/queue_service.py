import os
import uuid
from fastapi import HTTPException
from cache import REDIS_ENABLED, redis_client


WRITE_QUEUE_MODE = os.getenv("WRITE_QUEUE_MODE", "redis").lower()
WRITE_STREAM_KEY = os.getenv("WRITE_STREAM_KEY", "hn:write_events")


class WriteEventType:
    COMMENT_ADD = "comment.add"
    COMMENT_DELETE = "comment.delete"
    POST_VOTE_ADD = "post.vote.add"
    POST_VOTE_REMOVE = "post.vote.remove"
    COMMENT_VOTE_ADD = "comment.vote.add"
    COMMENT_VOTE_REMOVE = "comment.vote.remove"


def queue_writes_enabled() -> bool:
    return WRITE_QUEUE_MODE == "redis"


def enqueue_write(event_type: str, payload: dict) -> str:
    if not queue_writes_enabled():
        raise HTTPException(status_code=500, detail="Write queue is disabled")
    if not REDIS_ENABLED or redis_client is None:
        raise HTTPException(status_code=503, detail="Write queue is unavailable")

    request_id = str(uuid.uuid4())
    fields = {"type": event_type, "request_id": request_id}
    for key, value in payload.items():
        if value is None:
            continue
        fields[key] = str(value)

    try:
        redis_client.xadd(WRITE_STREAM_KEY, fields)
    except Exception as exc:  # RedisError is not always imported in tests.
        raise HTTPException(status_code=503, detail="Write queue is unavailable") from exc

    return request_id
