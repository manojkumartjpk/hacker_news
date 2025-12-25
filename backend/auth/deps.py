from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from auth import verify_token
from database import get_db
from services import UserService

oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=False)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def _get_token_from_request(request: Request, header_token: str | None) -> tuple[str | None, str | None]:
    if header_token:
        return header_token, "bearer"
    cookie_token = request.cookies.get("access_token")
    if cookie_token:
        return cookie_token, "cookie"
    return None, None

def _enforce_csrf(request: Request) -> None:
    csrf_cookie = request.cookies.get("csrf_token")
    csrf_header = request.headers.get("x-csrf-token")
    if not csrf_cookie or not csrf_header or csrf_cookie != csrf_header:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid CSRF token",
        )


def get_current_user_optional(
    request: Request,
    token: str | None = Depends(oauth2_scheme_optional),
    db: Session = Depends(get_db)
):
    """Return the authenticated user or None if no token is provided."""
    token_value, _ = _get_token_from_request(request, token)
    if not token_value:
        return None
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token_data = verify_token(token_value, credentials_exception)
    user = UserService.get_user_by_username(db, username=token_data.username)
    return user


def get_current_user(
    request: Request,
    token: str | None = Depends(oauth2_scheme_optional),
    db: Session = Depends(get_db)
):
    """Return the authenticated user or raise 401 for invalid credentials."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token_value, source = _get_token_from_request(request, token)
    if not token_value:
        raise credentials_exception
    if source == "cookie" and request.method in {"POST", "PUT", "PATCH", "DELETE"}:
        _enforce_csrf(request)
    token_data = verify_token(token_value, credentials_exception)
    user = UserService.get_user_by_username(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


def get_current_token(
    request: Request,
    token: str | None = Depends(oauth2_scheme_optional),
):
    """Return the current token from header or cookie, raising 401 if missing."""
    token_value, source = _get_token_from_request(request, token)
    if not token_value:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if source == "cookie" and request.method in {"POST", "PUT", "PATCH", "DELETE"}:
        _enforce_csrf(request)
    return token_value
