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


@pytest.mark.unit
def test_cache_helpers_swallow_redis_errors(monkeypatch):
    cache_module = importlib.reload(cache)
    monkeypatch.setattr(cache_module, "redis_client", _FailingRedis())

    assert cache_module.redis_get("k") is None
    assert cache_module.redis_setex("k", 10, "v") is None
    assert cache_module.redis_incr("k") is None
    assert cache_module.redis_expire("k", 10) is None
