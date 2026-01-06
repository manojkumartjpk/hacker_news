from fastapi import Request, HTTPException, Depends
from auth.deps import get_current_user_optional
from models import User
from cache import redis_get, redis_incr, redis_expire

def rate_limit():
    """Rate limiting dependency using Redis."""
    limit_user = 120
    limit_ip = 200
    window = 60
    def dependency(
        request: Request,
        current_user: User | None = Depends(get_current_user_optional)
    ):
        # Use user_id for authenticated requests, fallback to IP for guests.
        if current_user:
            key = f"rate_limit:user:{current_user.id}"
            effective_limit = limit_user
        else:
            client_ip = request.client.host if request.client else "unknown"
            key = f"rate_limit:ip:{client_ip}"
            effective_limit = limit_ip

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
