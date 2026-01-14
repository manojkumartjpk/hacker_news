import uuid

import pytest
from fastapi import HTTPException

from services import queue_service


class _FakeRedis:
    def __init__(self):
        self.messages = []

    def xadd(self, stream, fields):
        self.messages.append((stream, fields))


@pytest.mark.unit
def test_enqueue_write_sends_payload_and_returns_request_id(monkeypatch):
    fake_redis = _FakeRedis()
    monkeypatch.setattr(queue_service, "WRITE_QUEUE_MODE", "redis")
    monkeypatch.setattr(queue_service, "REDIS_ENABLED", True)
    monkeypatch.setattr(queue_service, "redis_client", fake_redis)

    request_id = queue_service.enqueue_write(
        queue_service.WriteEventType.POST_VOTE_ADD,
        {"user_id": 12, "post_id": 34, "note": None},
    )

    uuid.UUID(request_id)
    assert fake_redis.messages
    stream, fields = fake_redis.messages[0]
    assert stream == queue_service.WRITE_STREAM_KEY
    assert fields["type"] == queue_service.WriteEventType.POST_VOTE_ADD
    assert fields["user_id"] == "12"
    assert fields["post_id"] == "34"
    assert "note" not in fields


@pytest.mark.unit
def test_enqueue_write_disabled(monkeypatch):
    monkeypatch.setattr(queue_service, "WRITE_QUEUE_MODE", "sync")
    with pytest.raises(HTTPException) as exc:
        queue_service.enqueue_write(queue_service.WriteEventType.POST_VOTE_ADD, {"user_id": 1, "post_id": 2})
    assert exc.value.status_code == 500


@pytest.mark.unit
def test_enqueue_write_unavailable(monkeypatch):
    monkeypatch.setattr(queue_service, "WRITE_QUEUE_MODE", "redis")
    monkeypatch.setattr(queue_service, "REDIS_ENABLED", False)
    monkeypatch.setattr(queue_service, "redis_client", None)
    with pytest.raises(HTTPException) as exc:
        queue_service.enqueue_write(queue_service.WriteEventType.POST_VOTE_ADD, {"user_id": 1, "post_id": 2})
    assert exc.value.status_code == 503
