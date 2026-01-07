import pytest


@pytest.mark.unit
def test_create_comments_threaded(client, auth_headers):
    post_response = client.post(
        "/posts/",
        json={"title": "Threaded post", "text": "Body", "url": None},
        headers=auth_headers,
    )
    post_id = post_response.json()["id"]

    comment_response = client.post(
        f"/posts/{post_id}/comments",
        json={"text": "Top level comment", "parent_id": None},
        headers=auth_headers,
    )
    assert comment_response.status_code == 200
    comment_id = comment_response.json()["id"]

    reply_response = client.post(
        f"/posts/{post_id}/comments",
        json={"text": "Reply", "parent_id": comment_id},
        headers=auth_headers,
    )
    assert reply_response.status_code == 200

    thread_response = client.get(f"/posts/{post_id}/comments")
    assert thread_response.status_code == 200
    thread = thread_response.json()
    assert len(thread) == 1
    top_comment = thread[0]
    reply_comment = top_comment["replies"][0]
    assert reply_comment["text"] == "Reply"
    assert top_comment["root_id"] == top_comment["id"]
    assert reply_comment["root_id"] == top_comment["id"]
    assert top_comment["prev_id"] is None
    assert top_comment["next_id"] == reply_comment["id"]
    assert reply_comment["prev_id"] == top_comment["id"]
    assert reply_comment["next_id"] is None


@pytest.mark.unit
def test_update_comment_requires_owner(client, auth_headers, make_user):
    post_response = client.post(
        "/posts/",
        json={"title": "Editable post", "text": "Body", "url": None},
        headers=auth_headers,
    )
    post_id = post_response.json()["id"]

    comment_response = client.post(
        f"/posts/{post_id}/comments",
        json={"text": "Original", "parent_id": None},
        headers=auth_headers,
    )
    comment_id = comment_response.json()["id"]

    other_user = make_user(username="gina")
    other_login = client.post(
        "/auth/login",
        json={"username": other_user["username"], "password": other_user["password"]},
    )
    other_headers = {"Authorization": f"Bearer {other_login.json()['access_token']}"}

    update_response = client.put(
        f"/comments/{comment_id}",
        json={"text": "Hacked"},
        headers=other_headers,
    )
    assert update_response.status_code == 403
    assert update_response.json()["detail"] == "Not authorized to update this comment"


@pytest.mark.unit
def test_vote_on_comment(client, auth_headers):
    post_response = client.post(
        "/posts/",
        json={"title": "Comment vote post", "text": "Body", "url": None},
        headers=auth_headers,
    )
    post_id = post_response.json()["id"]

    comment_response = client.post(
        f"/posts/{post_id}/comments",
        json={"text": "Vote me", "parent_id": None},
        headers=auth_headers,
    )
    comment_id = comment_response.json()["id"]

    vote_response = client.post(
        f"/comments/{comment_id}/vote",
        json={"vote_type": 1},
        headers=auth_headers,
    )
    assert vote_response.status_code == 200
    assert vote_response.json()["vote_type"] == 1

    get_vote_response = client.get(f"/comments/{comment_id}/vote", headers=auth_headers)
    assert get_vote_response.status_code == 200
    assert get_vote_response.json()["vote_type"] == 1

    delete_vote_response = client.delete(f"/comments/{comment_id}/vote", headers=auth_headers)
    assert delete_vote_response.status_code == 200
    assert delete_vote_response.json()["vote_type"] == 0

    get_vote_after_delete = client.get(f"/comments/{comment_id}/vote", headers=auth_headers)
    assert get_vote_after_delete.status_code == 200
    assert get_vote_after_delete.json()["vote_type"] == 0


@pytest.mark.unit
def test_vote_on_comment_rejects_invalid_value(client, auth_headers):
    post_response = client.post(
        "/posts/",
        json={"title": "Bad vote", "text": "Body", "url": None},
        headers=auth_headers,
    )
    post_id = post_response.json()["id"]
    comment_response = client.post(
        f"/posts/{post_id}/comments",
        json={"text": "Vote me", "parent_id": None},
        headers=auth_headers,
    )
    comment_id = comment_response.json()["id"]
    vote_response = client.post(
        f"/comments/{comment_id}/vote",
        json={"vote_type": 0},
        headers=auth_headers,
    )
    assert vote_response.status_code == 400
    assert vote_response.json()["detail"] == "Vote type must be 1 (upvote)"


def test_get_comment_detail(client, auth_headers):
    post_response = client.post(
        "/posts/",
        headers=auth_headers,
        json={"title": "Detail post", "text": "Body", "url": None},
    )
    assert post_response.status_code == 200
    post_id = post_response.json()["id"]

    comment_response = client.post(
        f"/posts/{post_id}/comments",
        headers=auth_headers,
        json={"text": "Detail comment", "parent_id": None},
    )
    assert comment_response.status_code == 200
    comment_id = comment_response.json()["id"]

    detail_response = client.get(f"/comments/{comment_id}")
    assert detail_response.status_code == 200
    body = detail_response.json()
    assert body["id"] == comment_id
    assert body["post_id"] == post_id
    assert body["text"] == "Detail comment"
    assert body["root_id"] == comment_id


@pytest.mark.unit
def test_recent_comments(client, auth_headers):
    post_response = client.post(
        "/posts/",
        json={"title": "Recent comments post", "text": "Body", "url": None},
        headers=auth_headers,
    )
    post_id = post_response.json()["id"]

    client.post(
        f"/posts/{post_id}/comments",
        json={"text": "Recent comment", "parent_id": None},
        headers=auth_headers,
    )

    response = client.get("/comments/recent", params={"limit": 10})
    assert response.status_code == 200
    assert len(response.json()) >= 1


@pytest.mark.unit
def test_update_comment_success(client, auth_headers):
    post_response = client.post(
        "/posts/",
        json={"title": "Update comment post", "text": "Body", "url": None},
        headers=auth_headers,
    )
    post_id = post_response.json()["id"]
    comment_response = client.post(
        f"/posts/{post_id}/comments",
        json={"text": "Original", "parent_id": None},
        headers=auth_headers,
    )
    comment_id = comment_response.json()["id"]
    update_response = client.put(
        f"/comments/{comment_id}",
        json={"text": "Updated"},
        headers=auth_headers,
    )
    assert update_response.status_code == 200
    assert update_response.json()["text"] == "Updated"


@pytest.mark.unit
def test_delete_comment_success(client, auth_headers):
    post_response = client.post(
        "/posts/",
        json={"title": "Delete comment post", "text": "Body", "url": None},
        headers=auth_headers,
    )
    post_id = post_response.json()["id"]
    comment_response = client.post(
        f"/posts/{post_id}/comments",
        json={"text": "Delete me", "parent_id": None},
        headers=auth_headers,
    )
    comment_id = comment_response.json()["id"]
    delete_response = client.delete(f"/comments/{comment_id}", headers=auth_headers)
    assert delete_response.status_code == 204
    thread_response = client.get(f"/posts/{post_id}/comments")
    assert thread_response.status_code == 200
    deleted_comment = next(comment for comment in thread_response.json() if comment["id"] == comment_id)
    assert deleted_comment["is_deleted"] is True
    assert deleted_comment["text"] == "[deleted]"
