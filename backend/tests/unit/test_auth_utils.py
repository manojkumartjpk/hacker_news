import pytest
from fastapi import HTTPException

from auth import create_access_token, verify_token, get_password_hash, verify_password


@pytest.mark.unit
def test_password_hash_and_verify():
    password = "Password1!"
    hashed = get_password_hash(password)
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword1!", hashed) is False


@pytest.mark.unit
def test_create_and_verify_token_round_trip():
    token = create_access_token({"sub": "alice"})
    credentials_exception = HTTPException(status_code=401, detail="invalid")
    data = verify_token(token, credentials_exception)
    assert data.username == "alice"


@pytest.mark.unit
def test_verify_token_rejects_invalid_token():
    credentials_exception = HTTPException(status_code=401, detail="invalid")
    with pytest.raises(HTTPException):
        verify_token("not-a-token", credentials_exception)
