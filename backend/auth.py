from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
import hashlib
import os
from schemas import TokenData
import cache

# JWT settings
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY is required")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__ident="2b",
)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    # bcrypt has a 72 byte limit, so truncate if necessary
    return pwd_context.hash(password[:72])

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str, credentials_exception):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        if is_token_revoked(token):
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    return token_data

def _revocation_key(token: str) -> str:
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    return f"revoked:{token_hash}"

def revoke_token(token: str) -> None:
    try:
        claims = jwt.get_unverified_claims(token)
    except JWTError:
        return

    exp = claims.get("exp")
    if exp is None:
        ttl_seconds = ACCESS_TOKEN_EXPIRE_MINUTES * 60
    else:
        now = datetime.utcnow().timestamp()
        ttl_seconds = max(int(exp - now), 1)

    cache.redis_setex(_revocation_key(token), ttl_seconds, "1")

def is_token_revoked(token: str) -> bool:
    return cache.redis_get(_revocation_key(token)) is not None
