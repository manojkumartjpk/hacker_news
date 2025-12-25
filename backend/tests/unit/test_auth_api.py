import pytest


@pytest.mark.unit
def test_register_login_success(client):
    register_response = client.post(
        "/auth/register",
        json={"username": "alice", "email": "alice@example.com", "password": "Password1!"},
    )
    assert register_response.status_code == 200
    data = register_response.json()
    assert data["username"] == "alice"
    assert data["email"] == "alice@example.com"

    login_response = client.post(
        "/auth/login",
        json={"username": "alice", "password": "Password1!"},
    )
    assert login_response.status_code == 200
    assert login_response.json()["access_token"]


@pytest.mark.unit
def test_login_rejects_invalid_password(client, make_user):
    make_user(username="bob")
    response = client.post(
        "/auth/login",
        json={"username": "bob", "password": "wrong-password"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect username or password"


@pytest.mark.unit
def test_username_available(client, make_user):
    make_user(username="charlie")
    response_existing = client.get("/auth/username-available", params={"username": "charlie"})
    assert response_existing.status_code == 200
    assert response_existing.json()["available"] is False

    response_new = client.get("/auth/username-available", params={"username": "dana"})
    assert response_new.status_code == 200
    assert response_new.json()["available"] is True


@pytest.mark.unit
def test_me_requires_auth(client):
    response = client.get("/auth/me")
    assert response.status_code == 401


@pytest.mark.unit
def test_me_returns_user(client, auth_headers):
    response = client.get("/auth/me", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["username"] == "alice"


@pytest.mark.unit
def test_register_rejects_duplicate_username(client, make_user):
    make_user(username="alice", email="alice@example.com")
    response = client.post(
        "/auth/register",
        json={"username": "alice", "email": "other@example.com", "password": "Password1!"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Username already registered"


@pytest.mark.unit
def test_register_rejects_duplicate_email(client, make_user):
    make_user(username="alice", email="alice@example.com")
    response = client.post(
        "/auth/register",
        json={"username": "different", "email": "alice@example.com", "password": "Password1!"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"


@pytest.mark.unit
def test_register_rejects_short_password(client):
    response = client.post(
        "/auth/register",
        json={"username": "shorty", "email": "shorty@example.com", "password": "Short1!"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Password must be at least 9 characters."
