import pytest


@pytest.mark.integration
def test_end_to_end_user_flow(client, make_user):
    author = make_user(username="author")
    author_login = client.post(
        "/auth/login",
        json={"username": author["username"], "password": author["password"]},
    )
    author_headers = {"Authorization": f"Bearer {author_login.json()['access_token']}"}

    reader = make_user(username="reader")
    reader_login = client.post(
        "/auth/login",
        json={"username": reader["username"], "password": reader["password"]},
    )
    reader_headers = {"Authorization": f"Bearer {reader_login.json()['access_token']}"}

    post_response = client.post(
        "/posts/",
        json={"title": "End-to-end post", "text": "Story", "url": None},
        headers=author_headers,
    )
    post_id = post_response.json()["id"]

    comment_response = client.post(
        f"/posts/{post_id}/comments",
        json={"text": "First comment", "parent_id": None},
        headers=reader_headers,
    )
    comment_id = comment_response.json()["id"]

    vote_response = client.post(
        f"/posts/{post_id}/vote",
        json={"vote_type": 1},
        headers=reader_headers,
    )
    assert vote_response.status_code == 200

    comment_vote_response = client.post(
        f"/comments/{comment_id}/vote",
        json={"vote_type": 1},
        headers=author_headers,
    )
    assert comment_vote_response.status_code == 200

    unread_response = client.get("/notifications/unread/count", headers=author_headers)
    assert unread_response.status_code == 200
    assert unread_response.json()["unread_count"] == 1

    notifications_response = client.get("/notifications", headers=author_headers)
    notification_id = notifications_response.json()[0]["id"]

    mark_read_response = client.put(f"/notifications/{notification_id}/read", headers=author_headers)
    assert mark_read_response.status_code == 200

    unread_after = client.get("/notifications/unread/count", headers=author_headers)
    assert unread_after.status_code == 200
    assert unread_after.json()["unread_count"] == 0
