import os
import redis

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")

# Use decode_responses so cached JSON strings are returned as str.
redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)


def redis_get(key: str):
    try:
        return redis_client.get(key)
    except redis.RedisError:
        return None


def redis_setex(key: str, ttl_seconds: int, value: str) -> None:
    try:
        redis_client.setex(key, ttl_seconds, value)
    except redis.RedisError:
        return None


def redis_incr(key: str) -> int | None:
    try:
        return int(redis_client.incr(key))
    except redis.RedisError:
        return None


def redis_expire(key: str, ttl_seconds: int) -> None:
    try:
        redis_client.expire(key, ttl_seconds)
    except redis.RedisError:
        return None
