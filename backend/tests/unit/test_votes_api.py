import pytest


@pytest.mark.unit
def test_vote_on_post_and_get_vote(client, auth_headers):
    post_response = client.post(
        "/posts/",
        json={"title": "Vote post", "url": "https://example.com", "text": None},
        headers=auth_headers,
    )
    post_id = post_response.json()["id"]

    vote_response = client.post(
        f"/posts/{post_id}/vote",
        json={"vote_type": 1},
        headers=auth_headers,
    )
    assert vote_response.status_code == 200
    assert vote_response.json()["vote_type"] == 1

    get_vote_response = client.get(f"/posts/{post_id}/vote", headers=auth_headers)
    assert get_vote_response.status_code == 200
    assert get_vote_response.json()["vote_type"] == 1

    delete_vote_response = client.delete(f"/posts/{post_id}/vote", headers=auth_headers)
    assert delete_vote_response.status_code == 200
    assert delete_vote_response.json()["vote_type"] == 0


@pytest.mark.unit
def test_vote_on_post_rejects_invalid_value(client, auth_headers):
    post_response = client.post(
        "/posts/",
        json={"title": "Vote post", "text": "Body", "url": None},
        headers=auth_headers,
    )
    post_id = post_response.json()["id"]

    vote_response = client.post(
        f"/posts/{post_id}/vote",
        json={"vote_type": 0},
        headers=auth_headers,
    )
    assert vote_response.status_code == 400
    assert vote_response.json()["detail"] == "Vote type must be 1 (upvote) or -1 (downvote)"


@pytest.mark.unit
def test_get_vote_requires_auth(client):
    response = client.get("/posts/1/vote")
    assert response.status_code == 401
