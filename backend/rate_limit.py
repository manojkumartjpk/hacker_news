import redis
import os
from fastapi import Request, HTTPException, Depends
import time

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")
redis_client = redis.Redis.from_url(REDIS_URL)

def rate_limit(limit: int = 100, window: int = 60):
    """
    Rate limiting dependency using Redis.
    limit: number of requests allowed
    window: time window in seconds
    """
    def dependency(request: Request):
        # Get client IP (in production, use proper IP extraction)
        client_ip = request.client.host if request.client else "unknown"

        # Redis key for this client
        key = f"rate_limit:{client_ip}"

        # Get current count
        current = redis_client.get(key)
        if current is None:
            current = 0
        else:
            current = int(current)

        # Check if limit exceeded
        if current >= limit:
            raise HTTPException(status_code=429, detail="Rate limit exceeded")

        # Increment counter
        redis_client.incr(key)

        # Set expiry if this is the first request in window
        if current == 0:
            redis_client.expire(key, window)

        return True

    return dependency