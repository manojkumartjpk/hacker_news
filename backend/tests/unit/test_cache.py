import importlib

import pytest
import redis

import cache


class _FailingRedis:
    def get(self, key):
        raise redis.RedisError("fail")

    def setex(self, key, ttl, value):
        raise redis.RedisError("fail")

    def incr(self, key):
        raise redis.RedisError("fail")

    def expire(self, key, ttl):
        raise redis.RedisError("fail")


class _WorkingRedis:
    def __init__(self):
        self.store = {}

    def get(self, key):
        return self.store.get(key)

    def setex(self, key, ttl, value):
        self.store[key] = value

    def incr(self, key):
        current = int(self.store.get(key, 0) or 0)
        current += 1
        self.store[key] = str(current)
        return current

    def expire(self, key, ttl):
        return True


@pytest.mark.unit
def test_cache_helpers_swallow_redis_errors(monkeypatch):
    cache_module = importlib.reload(cache)
    monkeypatch.setattr(cache_module, "redis_client", _FailingRedis())

    assert cache_module.redis_get("k") is None
    assert cache_module.redis_setex("k", 10, "v") is None
    assert cache_module.redis_incr("k") is None
    assert cache_module.redis_expire("k", 10) is None


@pytest.mark.unit
def test_cache_helpers_noop_when_disabled(monkeypatch):
    cache_module = importlib.reload(cache)
    monkeypatch.setattr(cache_module, "REDIS_ENABLED", False)
    monkeypatch.setattr(cache_module, "redis_client", None)

    assert cache_module.redis_get("k") is None
    assert cache_module.redis_setex("k", 10, "v") is None
    assert cache_module.redis_incr("k") is None
    assert cache_module.redis_expire("k", 10) is None


@pytest.mark.unit
def test_cache_helpers_success(monkeypatch):
    cache_module = importlib.reload(cache)
    monkeypatch.setattr(cache_module, "REDIS_ENABLED", True)
    monkeypatch.setattr(cache_module, "redis_client", _WorkingRedis())

    assert cache_module.redis_get("k") is None
    assert cache_module.redis_setex("k", 10, "v") is None
    assert cache_module.redis_get("k") == "v"
    assert cache_module.redis_incr("counter") == 1
    assert cache_module.redis_expire("counter", 10) is None
