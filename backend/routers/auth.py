from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from datetime import timedelta
import secrets
from database import get_db
from auth import create_access_token, revoke_token, verify_token, ACCESS_TOKEN_EXPIRE_MINUTES
from auth.deps import get_current_user, get_current_token
from schemas import UserCreate, User, Token, UserLogin, Availability, Message
from services import UserService
from rate_limit import rate_limit

router = APIRouter()

@router.post("/register", response_model=User)
def register(
    user: UserCreate,
    db: Session = Depends(get_db),
    rate_limited: bool = Depends(rate_limit())
):
    """Register a new user account."""
    return UserService.create_user(db, user)

@router.post("/login", response_model=Token)
def login(
    user_credentials: UserLogin,
    response: Response,
    db: Session = Depends(get_db),
    rate_limited: bool = Depends(rate_limit())
):
    """Authenticate a user and return a bearer token."""
    user = UserService.authenticate_user(db, user_credentials.username, user_credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    csrf_token = secrets.token_urlsafe(32)
    max_age = ACCESS_TOKEN_EXPIRE_MINUTES * 60
    response.set_cookie(
        "access_token",
        access_token,
        httponly=True,
        samesite="lax",
        max_age=max_age,
        secure=False,
    )
    response.set_cookie(
        "csrf_token",
        csrf_token,
        httponly=False,
        samesite="lax",
        max_age=max_age,
        secure=False,
    )
    response.set_cookie(
        "auth_status",
        "1",
        httponly=False,
        samesite="lax",
        max_age=max_age,
        secure=False,
    )
    response.headers["X-CSRF-Token"] = csrf_token
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/username-available", response_model=Availability)
def username_available(
    username: str,
    db: Session = Depends(get_db),
    rate_limited: bool = Depends(rate_limit())
):
    """Check if a username is available for registration."""
    user = UserService.get_user_by_username(db, username=username)
    return {"available": user is None}


@router.get("/me", response_model=User)
def get_me(
    current_user: User = Depends(get_current_user),
    rate_limited: bool = Depends(rate_limit())
):
    """Return the currently authenticated user."""
    return current_user


@router.post("/logout", response_model=Message)
def logout(
    response: Response,
    token: str = Depends(get_current_token),
    rate_limited: bool = Depends(rate_limit())
):
    """Revoke the current access token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    verify_token(token, credentials_exception)
    revoke_token(token)
    response.delete_cookie("access_token")
    response.delete_cookie("csrf_token")
    response.delete_cookie("auth_status")
    return {"message": "Logged out"}
