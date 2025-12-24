import pytest


@pytest.mark.unit
def test_create_post_requires_content(client, auth_headers):
    response = client.post(
        "/posts/",
        json={"title": "Empty", "url": None, "text": None},
        headers=auth_headers,
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Post must have either a URL or text content"


@pytest.mark.unit
def test_create_and_fetch_post(client, auth_headers):
    create_response = client.post(
        "/posts/",
        json={"title": "Hello HN", "url": "https://example.com", "text": None},
        headers=auth_headers,
    )
    assert create_response.status_code == 200
    post = create_response.json()
    assert post["title"] == "Hello HN"

    detail_response = client.get(f"/posts/{post['id']}")
    assert detail_response.status_code == 200
    assert detail_response.json()["id"] == post["id"]


@pytest.mark.unit
def test_search_posts_returns_matches(client, auth_headers):
    client.post(
        "/posts/",
        json={"title": "Searchable title", "text": "Some text", "url": None},
        headers=auth_headers,
    )
    response = client.get("/posts/search", params={"q": "Searchable"})
    assert response.status_code == 200
    assert len(response.json()) == 1


@pytest.mark.unit
def test_update_post_requires_owner(client, auth_headers, make_user):
    other_user = make_user(username="erin")
    other_login = client.post(
        "/auth/login",
        json={"username": other_user["username"], "password": other_user["password"]},
    )
    other_headers = {"Authorization": f"Bearer {other_login.json()['access_token']}"}

    create_response = client.post(
        "/posts/",
        json={"title": "Owned post", "text": "Body", "url": None},
        headers=auth_headers,
    )
    post_id = create_response.json()["id"]

    response = client.put(
        f"/posts/{post_id}",
        json={"title": "Hacked title"},
        headers=other_headers,
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Not authorized to update this post"


@pytest.mark.unit
def test_delete_post_requires_owner(client, auth_headers, make_user):
    other_user = make_user(username="frank")
    other_login = client.post(
        "/auth/login",
        json={"username": other_user["username"], "password": other_user["password"]},
    )
    other_headers = {"Authorization": f"Bearer {other_login.json()['access_token']}"}

    create_response = client.post(
        "/posts/",
        json={"title": "Owned post", "text": "Body", "url": None},
        headers=auth_headers,
    )
    post_id = create_response.json()["id"]

    response = client.delete(f"/posts/{post_id}", headers=other_headers)
    assert response.status_code == 403
    assert response.json()["detail"] == "Not authorized to delete this post"
