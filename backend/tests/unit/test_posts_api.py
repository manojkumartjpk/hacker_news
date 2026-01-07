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
def test_get_posts_filters_by_post_type(client, auth_headers):
    client.post(
        "/posts/",
        json={"title": "Story post", "url": "https://example.com", "text": None, "post_type": "story"},
        headers=auth_headers,
    )
    client.post(
        "/posts/",
        json={"title": "Show post", "url": "https://example.com/show", "text": None, "post_type": "show"},
        headers=auth_headers,
    )
    response = client.get("/posts/", params={"post_type": "show"})
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["post_type"] == "show"

