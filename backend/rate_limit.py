from fastapi import Request, HTTPException, Depends
from auth.deps import get_current_user_optional
from models import User
from cache import redis_get, redis_incr, redis_expire

def rate_limit(limit: int = 100, window: int = 60):
    """
    Rate limiting dependency using Redis.
    limit: number of requests allowed
    window: time window in seconds
    """
    def dependency(
        request: Request,
        current_user: User | None = Depends(get_current_user_optional)
    ):
        # Use user_id for authenticated requests, fallback to IP for guests.
        if current_user:
            key = f"rate_limit:user:{current_user.id}"
            effective_limit = 60
        else:
            client_ip = request.client.host if request.client else "unknown"
            key = f"rate_limit:ip:{client_ip}"
            effective_limit = limit

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
        if current >= effective_limit:
            raise HTTPException(status_code=429, detail="Rate limit exceeded")

        # Increment counter
        redis_incr(key)

        # Set expiry if this is the first request in window
        if current == 0:
            redis_expire(key, window)

        return True

    return dependency
