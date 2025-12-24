import pytest


@pytest.mark.unit
def test_notifications_created_for_comments(client, make_user):
    author = make_user(username="henry")
    author_login = client.post(
        "/auth/login",
        json={"username": author["username"], "password": author["password"]},
    )
    author_headers = {"Authorization": f"Bearer {author_login.json()['access_token']}"}

    commenter = make_user(username="ivy")
    commenter_login = client.post(
        "/auth/login",
        json={"username": commenter["username"], "password": commenter["password"]},
    )
    commenter_headers = {"Authorization": f"Bearer {commenter_login.json()['access_token']}"}

    post_response = client.post(
        "/posts/",
        json={"title": "Notify post", "text": "Body", "url": None},
        headers=author_headers,
    )
    post_id = post_response.json()["id"]

    client.post(
        f"/posts/{post_id}/comments",
        json={"text": "Nice post!", "parent_id": None},
        headers=commenter_headers,
    )

    unread_response = client.get("/notifications/unread/count", headers=author_headers)
    assert unread_response.status_code == 200
    assert unread_response.json()["unread_count"] == 1

    notifications_response = client.get("/notifications", headers=author_headers)
    assert notifications_response.status_code == 200
    notifications = notifications_response.json()
    assert len(notifications) == 1
    assert notifications[0]["actor_username"] == commenter["username"]
