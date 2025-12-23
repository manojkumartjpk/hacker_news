from fastapi import Request, HTTPException, Depends
from cache import redis_get, redis_incr, redis_expire

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
        current = redis_get(key)
        if current is None:
            current = 0
        else:
            try:
                current = int(current)
            except ValueError:
                current = 0

        # Check if limit exceeded
        if current >= limit:
            raise HTTPException(status_code=429, detail="Rate limit exceeded")

        # Increment counter
        redis_incr(key)

        # Set expiry if this is the first request in window
        if current == 0:
            redis_expire(key, window)

        return True

    return dependency
