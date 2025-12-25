import pytest
from fastapi import HTTPException
from pydantic import ValidationError

import services.post_service as post_service

from auth import get_password_hash
from models import User, Post
from schemas import PostCreate, PostUpdate, VoteCreate
from services.post_service import PostService
from services.vote_service import VoteService


@pytest.mark.unit
def test_create_post_rejects_invalid_type(db_session):
    user = User(username="alice", email="alice@example.com", hashed_password=get_password_hash("Password1!"))
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    with pytest.raises(ValidationError):
        PostCreate(title="Bad", url="https://example.com", text=None, post_type="invalid")


@pytest.mark.unit
def test_update_post_rejects_invalid_type(db_session):
    user = User(username="bob", email="bob@example.com", hashed_password=get_password_hash("Password1!"))
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    post = Post(title="Original", url=None, text="Body", post_type="story", user_id=user.id)
    db_session.add(post)
    db_session.commit()
    db_session.refresh(post)

    with pytest.raises(ValidationError):
        PostUpdate(post_type="invalid")


@pytest.mark.unit
def test_search_posts_empty_query_returns_empty(db_session):
    results = PostService.search_posts(db_session, query="   ", skip=0, limit=10)
    assert results == []


@pytest.mark.unit
def test_get_posts_caches_and_sorts(db_session):
    user = User(username="carol", email="carol@example.com", hashed_password=get_password_hash("Password1!"))
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    post_low = Post(title="Low", url=None, text="Body", post_type="story", user_id=user.id, score=1)
    post_high = Post(title="High", url=None, text="Body", post_type="story", user_id=user.id, score=10)
    db_session.add_all([post_low, post_high])
    db_session.commit()

    first = PostService.get_posts(db_session, sort="top", skip=0, limit=10, post_type=None)
    second = PostService.get_posts(db_session, sort="top", skip=0, limit=10, post_type=None)
    assert first[0]["title"] == "High"
    assert second[0]["title"] == "High"


@pytest.mark.unit
def test_get_post_missing(db_session):
    with pytest.raises(HTTPException):
        PostService.get_post(db_session, 999)


@pytest.mark.unit
def test_get_posts_handles_bad_cache(monkeypatch, db_session):
    user = User(username="cache", email="cache@example.com", hashed_password=get_password_hash("Password1!"))
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    post = Post(title="Cached", url=None, text="Body", post_type="story", user_id=user.id)
    db_session.add(post)
    db_session.commit()

    def fake_redis_get(key):
        if key.startswith("feed:"):
            return "{bad-json"
        return None

    monkeypatch.setattr(post_service, "redis_get", fake_redis_get)
    monkeypatch.setattr(post_service, "redis_setex", lambda *args, **kwargs: None)

    results = PostService.get_posts(db_session, sort="new", skip=0, limit=10, post_type=None)
    assert len(results) == 1


@pytest.mark.unit
def test_get_feed_cache_version_handles_bad_value(monkeypatch):
    monkeypatch.setattr(post_service, "redis_get", lambda key: "not-an-int")
    assert PostService._get_feed_cache_version() == 1


@pytest.mark.unit
def test_bump_feed_cache_version_noop(monkeypatch):
    monkeypatch.setattr(post_service, "redis_incr", lambda key: None)
    assert PostService.bump_feed_cache_version() is None


@pytest.mark.unit
def test_update_post_allows_null_post_type(db_session):
    user = User(username="nulltype", email="nulltype@example.com", hashed_password=get_password_hash("Password1!"))
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    post = Post(title="Original", url=None, text="Body", post_type="story", user_id=user.id)
    db_session.add(post)
    db_session.commit()
    db_session.refresh(post)

    updated = PostService.update_post(db_session, post.id, PostUpdate(post_type=None, title="Updated"), user.id)
    assert updated["post_type"] == "story"
    assert updated["title"] == "Updated"


@pytest.mark.unit
def test_update_post_missing(db_session):
    with pytest.raises(HTTPException):
        PostService.update_post(db_session, 999, PostUpdate(title="Nope"), 1)


@pytest.mark.unit
def test_delete_post_missing(db_session):
    with pytest.raises(HTTPException):
        PostService.delete_post(db_session, 999, 1)


@pytest.mark.unit
def test_get_cached_score_reads_redis(monkeypatch):
    monkeypatch.setattr(post_service, "redis_get", lambda key: "5")
    assert PostService.get_cached_score(1) == 5


@pytest.mark.unit
def test_get_cached_score_defaults_to_zero(monkeypatch):
    monkeypatch.setattr(post_service, "redis_get", lambda key: None)
    assert PostService.get_cached_score(123) == 0


@pytest.mark.unit
def test_update_post_score_recalculates(db_session):
    user = User(username="derek", email="derek@example.com", hashed_password=get_password_hash("Password1!"))
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    post = Post(title="Score", url=None, text="Body", post_type="story", user_id=user.id)
    db_session.add(post)
    db_session.commit()
    db_session.refresh(post)

    VoteService.vote_on_post(db_session, post.id, VoteCreate(vote_type=1), user.id)
    score = PostService.update_post_score(db_session, post.id)
    assert score == 1


@pytest.mark.unit
def test_delete_post_removes(db_session):
    user = User(username="emma", email="emma@example.com", hashed_password=get_password_hash("Password1!"))
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    post = Post(title="Delete", url=None, text="Body", post_type="story", user_id=user.id)
    db_session.add(post)
    db_session.commit()
    db_session.refresh(post)

    PostService.delete_post(db_session, post.id, user.id)
    assert db_session.query(Post).filter(Post.id == post.id).first() is None
