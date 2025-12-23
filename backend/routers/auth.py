from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta
from database import get_db
from auth import create_access_token
from auth.deps import get_current_user
from schemas import UserCreate, User, Token, UserLogin
from services import UserService
from rate_limit import rate_limit

router = APIRouter()

@router.post("/register", response_model=User)
def register(
    user: UserCreate,
    db: Session = Depends(get_db),
    rate_limited: bool = Depends(rate_limit(limit=10, window=60))  # 10 registrations per minute
):
    """Register a new user account."""
    return UserService.create_user(db, user)

@router.post("/login", response_model=Token)
def login(
    user_credentials: UserLogin,
    db: Session = Depends(get_db),
    rate_limited: bool = Depends(rate_limit(limit=10, window=60))  # 10 login attempts per minute
):
    """Authenticate a user and return a bearer token."""
    user = UserService.authenticate_user(db, user_credentials.username, user_credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/username-available")
def username_available(
    username: str,
    db: Session = Depends(get_db),
    rate_limited: bool = Depends(rate_limit(limit=10, window=60))
):
    """Check if a username is available for registration."""
    user = UserService.get_user_by_username(db, username=username)
    return {"available": user is None}


@router.get("/me", response_model=User)
def get_me(
    current_user: User = Depends(get_current_user),
    rate_limited: bool = Depends(rate_limit(limit=60, window=60))
):
    """Return the currently authenticated user."""
    return current_user
