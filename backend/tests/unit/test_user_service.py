import pytest
from fastapi import HTTPException

from schemas import UserCreate
from services.user_service import UserService


@pytest.mark.unit
def test_user_service_password_validation(db_session):
    with pytest.raises(HTTPException):
        UserService.create_user(
            db_session,
            UserCreate(username="weak", email="weak@example.com", password="short"),
        )

    with pytest.raises(HTTPException):
        UserService.create_user(
            db_session,
            UserCreate(username="weak2", email="weak2@example.com", password="password1!"),
        )

    with pytest.raises(HTTPException):
        UserService.create_user(
            db_session,
            UserCreate(username="weak3", email="weak3@example.com", password="Password!"),
        )

    with pytest.raises(HTTPException):
        UserService.create_user(
            db_session,
            UserCreate(username="weak4", email="weak4@example.com", password="Password1"),
        )


@pytest.mark.unit
def test_user_service_duplicate_username_and_email(db_session):
    user = UserService.create_user(
        db_session,
        UserCreate(username="dup", email="dup@example.com", password="Password1!"),
    )
    assert user.username == "dup"

    with pytest.raises(HTTPException):
        UserService.create_user(
            db_session,
            UserCreate(username="dup", email="dup2@example.com", password="Password1!"),
        )

    with pytest.raises(HTTPException):
        UserService.create_user(
            db_session,
            UserCreate(username="dup2", email="dup@example.com", password="Password1!"),
        )


@pytest.mark.unit
def test_user_service_authenticate_user(db_session):
    UserService.create_user(
        db_session,
        UserCreate(username="auth", email="auth@example.com", password="Password1!"),
    )
    assert UserService.authenticate_user(db_session, "auth", "Password1!") is not False
    assert UserService.authenticate_user(db_session, "auth", "Wrong1!") is False
    assert UserService.authenticate_user(db_session, "missing", "Password1!") is False
