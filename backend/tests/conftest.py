import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

os.environ.setdefault("POSTGRES_URL", "postgresql://user:password@postgres:5432/hackernews_test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379")

from main import app  # noqa: E402
from database import Base, engine, SessionLocal  # noqa: E402


@pytest.fixture(autouse=True)
def fake_redis(monkeypatch):
    store = {}

    def redis_get(key: str):
        return store.get(key)

    def redis_setex(key: str, ttl_seconds: int, value: str) -> None:
        store[key] = value

    def redis_incr(key: str) -> int:
        current = int(store.get(key, 0) or 0)
        current += 1
        store[key] = str(current)
        return current

    def redis_expire(key: str, ttl_seconds: int) -> None:
        return None

    import cache
    import rate_limit
    from services import post_service

    monkeypatch.setattr(cache, "redis_get", redis_get)
    monkeypatch.setattr(cache, "redis_setex", redis_setex)
    monkeypatch.setattr(cache, "redis_incr", redis_incr)
    monkeypatch.setattr(cache, "redis_expire", redis_expire)
    monkeypatch.setattr(rate_limit, "redis_get", redis_get)
    monkeypatch.setattr(rate_limit, "redis_incr", redis_incr)
    monkeypatch.setattr(rate_limit, "redis_expire", redis_expire)
    monkeypatch.setattr(post_service, "redis_get", redis_get)
    monkeypatch.setattr(post_service, "redis_setex", redis_setex)
    monkeypatch.setattr(post_service, "redis_incr", redis_incr)

    yield


@pytest.fixture()
def client():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    with TestClient(app) as test_client:
        yield test_client

    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db_session():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def make_user(client):
    def _make_user(username="alice", email=None, password="Password1!"):
        if email is None:
            email = f"{username}@example.com"
        response = client.post(
            "/auth/register",
            json={"username": username, "email": email, "password": password},
        )
        assert response.status_code == 200
        return {"username": username, "password": password, "email": email}

    return _make_user


@pytest.fixture()
def auth_headers(client, make_user):
    credentials = make_user()
    login_response = client.post(
        "/auth/login",
        json={"username": credentials["username"], "password": credentials["password"]},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
