def test_root(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Hacker News Clone API"


def test_register_login_post_vote_flow(client):
    register_response = client.post(
        "/auth/register",
        json={"username": "alice", "email": "alice@example.com", "password": "password123"},
    )
    assert register_response.status_code == 200

    login_response = client.post(
        "/auth/login",
        json={"username": "alice", "password": "password123"},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    post_response = client.post(
        "/posts/",
        json={"title": "Hello HN", "url": "https://example.com", "text": None},
        headers=headers,
    )
    assert post_response.status_code == 200
    post_id = post_response.json()["id"]

    list_response = client.get("/posts/", params={"sort": "new", "limit": 10})
    assert list_response.status_code == 200
    assert len(list_response.json()) >= 1

    vote_response = client.post(
        f"/posts/{post_id}/vote",
        json={"vote_type": 1},
        headers=headers,
    )
    assert vote_response.status_code == 200

    detail_response = client.get(f"/posts/{post_id}")
    assert detail_response.status_code == 200
    assert detail_response.json()["score"] >= 1
