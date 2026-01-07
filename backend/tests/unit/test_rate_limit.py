import pytest
from fastapi import HTTPException

import rate_limit


class _Client:
    def __init__(self, host):
        self.host = host


class _Request:
    def __init__(self, host="127.0.0.1"):
        self.client = _Client(host)


@pytest.mark.unit
def test_rate_limit_tracks_ip(monkeypatch):
    store = {}

    def redis_get(key):
        return store.get(key)

    def redis_incr(key):
        store[key] = str(int(store.get(key, 0)) + 1)
        return int(store[key])

    def redis_expire(key, ttl):
        return None

    monkeypatch.setattr(rate_limit, "redis_get", redis_get)
    monkeypatch.setattr(rate_limit, "redis_incr", redis_incr)
    monkeypatch.setattr(rate_limit, "redis_expire", redis_expire)

    dependency = rate_limit.rate_limit()
    for _ in range(200):
        dependency(_Request(), None)
    with pytest.raises(HTTPException):
        dependency(_Request(), None)


@pytest.mark.unit
def test_rate_limit_tracks_user(monkeypatch):
    store = {}

    def redis_get(key):
        return store.get(key)

    def redis_incr(key):
        store[key] = str(int(store.get(key, 0)) + 1)
        return int(store[key])

    def redis_expire(key, ttl):
        return None

    monkeypatch.setattr(rate_limit, "redis_get", redis_get)
    monkeypatch.setattr(rate_limit, "redis_incr", redis_incr)
    monkeypatch.setattr(rate_limit, "redis_expire", redis_expire)

    dependency = rate_limit.rate_limit()
    user = type("User", (), {"id": 42})()
    for _ in range(120):
        dependency(_Request(), user)
    with pytest.raises(HTTPException):
        dependency(_Request(), user)


@pytest.mark.unit
def test_rate_limit_handles_bad_counter(monkeypatch):
    def redis_get(key):
        return "not-an-int"

    def redis_incr(key):
        return 1

    def redis_expire(key, ttl):
        return None

    monkeypatch.setattr(rate_limit, "redis_get", redis_get)
    monkeypatch.setattr(rate_limit, "redis_incr", redis_incr)
    monkeypatch.setattr(rate_limit, "redis_expire", redis_expire)

    dependency = rate_limit.rate_limit()
    dependency(_Request(), None)
