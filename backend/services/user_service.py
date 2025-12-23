from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from models import User
from schemas import UserCreate
from auth import get_password_hash, verify_password
from fastapi import HTTPException

class UserService:
    @staticmethod
    def _validate_password(password: str) -> None:
        if len(password) < 9:
            raise HTTPException(status_code=400, detail="Password must be at least 9 characters.")
        if not any(char.isupper() for char in password):
            raise HTTPException(status_code=400, detail="Password must include at least one uppercase letter.")
        if not any(char.isdigit() for char in password):
            raise HTTPException(status_code=400, detail="Password must include at least one number.")
        if not any(not char.isalnum() for char in password):
            raise HTTPException(status_code=400, detail="Password must include at least one special character.")

    @staticmethod
    def create_user(db: Session, user: UserCreate) -> User:
        UserService._validate_password(user.password)
        # Check if username or email already exists
        existing_user = db.query(User).filter(
            (User.username == user.username) | (User.email == user.email)
        ).first()
        if existing_user:
            if existing_user.username == user.username:
                raise HTTPException(status_code=400, detail="Username already registered")
            else:
                raise HTTPException(status_code=400, detail="Email already registered")

        hashed_password = get_password_hash(user.password)
        db_user = User(
            username=user.username,
            email=user.email,
            hashed_password=hashed_password
        )
        db.add(db_user)
        try:
            db.commit()
            db.refresh(db_user)
            return db_user
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=400, detail="User creation failed")

    @staticmethod
    def get_user_by_username(db: Session, username: str) -> User:
        return db.query(User).filter(User.username == username).first()

    @staticmethod
    def authenticate_user(db: Session, username: str, password: str) -> User:
        user = UserService.get_user_by_username(db, username)
        if not user:
            return False
        if not verify_password(password, user.hashed_password):
            return False
        return user
