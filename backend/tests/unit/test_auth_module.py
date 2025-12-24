import importlib.util
from pathlib import Path

import pytest
from fastapi import HTTPException


def _load_auth_module():
    module_path = Path(__file__).resolve().parents[2] / "auth.py"
    spec = importlib.util.spec_from_file_location("auth_module_file", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.unit
def test_auth_module_token_round_trip():
    auth_module = _load_auth_module()
    token = auth_module.create_access_token({"sub": "tester"})
    credentials_exception = HTTPException(status_code=401, detail="invalid")
    data = auth_module.verify_token(token, credentials_exception)
    assert data["username"] == "tester"


@pytest.mark.unit
def test_auth_module_rejects_invalid_token():
    auth_module = _load_auth_module()
    credentials_exception = HTTPException(status_code=401, detail="invalid")
    with pytest.raises(HTTPException):
        auth_module.verify_token("bad-token", credentials_exception)


def test_auth_module_password_hashing_and_verify():
    auth_module = _load_auth_module()
    password = "Password1!"
    hashed = auth_module.get_password_hash(password)
    assert hashed != password
    assert auth_module.verify_password(password, hashed) is True
    assert auth_module.verify_password("Wrong1!", hashed) is False


def test_auth_module_token_default_expiry_and_missing_sub():
    auth_module = _load_auth_module()
    token = auth_module.create_access_token({"sub": "tester"}, expires_delta=None)
    credentials_exception = HTTPException(status_code=401, detail="invalid")
    data = auth_module.verify_token(token, credentials_exception)
    assert data["username"] == "tester"

    token_without_sub = auth_module.create_access_token({})
    with pytest.raises(HTTPException):
        auth_module.verify_token(token_without_sub, credentials_exception)


def test_auth_module_token_with_custom_expiry():
    auth_module = _load_auth_module()
    token = auth_module.create_access_token(
        {"sub": "tester"}, expires_delta=auth_module.timedelta(minutes=5)
    )
    credentials_exception = HTTPException(status_code=401, detail="invalid")
    data = auth_module.verify_token(token, credentials_exception)
    assert data["username"] == "tester"
