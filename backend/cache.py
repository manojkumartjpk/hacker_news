import os
import redis

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")
REDIS_ENABLED = os.getenv("REDIS_ENABLED", "1").lower() not in {"0", "false", "no", "off"}

# Use decode_responses so cached JSON strings are returned as str.
redis_client = (
    redis.Redis.from_url(REDIS_URL, decode_responses=True)
    if REDIS_ENABLED
    else None
)


def redis_get(key: str):
    if not REDIS_ENABLED or redis_client is None:
        return None
    try:
        return redis_client.get(key)
    except redis.RedisError:
        return None


def redis_setex(key: str, ttl_seconds: int, value: str) -> None:
    if not REDIS_ENABLED or redis_client is None:
        return None
    try:
        redis_client.setex(key, ttl_seconds, value)
    except redis.RedisError:
        return None


def redis_incr(key: str) -> int | None:
    if not REDIS_ENABLED or redis_client is None:
        return None
    try:
        return int(redis_client.incr(key))
    except redis.RedisError:
        return None


def redis_expire(key: str, ttl_seconds: int) -> None:
    if not REDIS_ENABLED or redis_client is None:
        return None
    try:
        redis_client.expire(key, ttl_seconds)
    except redis.RedisError:
        return None
