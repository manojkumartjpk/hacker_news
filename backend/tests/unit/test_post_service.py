from datetime import date, datetime, timezone
import pytest
from fastapi import HTTPException
from pydantic import ValidationError

import services.post_service as post_service

from auth import get_password_hash
from models import User, Post
from schemas import PostCreate, VoteCreate
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
def test_search_posts_empty_query_returns_empty(db_session):
    results = PostService.search_posts(db_session, query="   ", skip=0, limit=10)
    assert results == []


@pytest.mark.unit
def test_get_posts_caches_and_sorts(db_session):
    user = User(username="carol", email="carol@example.com", hashed_password=get_password_hash("Password1!"))
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    post_low = Post(title="Low", url=None, text="Body", post_type="story", user_id=user.id, points=1)
    post_high = Post(title="High", url=None, text="Body", post_type="story", user_id=user.id, points=10)
    db_session.add_all([post_low, post_high])
    db_session.commit()

    first = PostService.get_posts(db_session, sort="past", skip=0, limit=10, post_type=None)
    second = PostService.get_posts(db_session, sort="past", skip=0, limit=10, post_type=None)
    assert first[0]["title"] == "High"
    assert second[0]["title"] == "High"


@pytest.mark.unit
def test_get_posts_filters_by_day_when_past(db_session):
    user = User(username="day", email="day@example.com", hashed_password=get_password_hash("Password1!"))
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    post_day1 = Post(
        title="Day One",
        url=None,
        text="Body",
        post_type="story",
        user_id=user.id,
        created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
    )
    post_day2 = Post(
        title="Day Two",
        url=None,
        text="Body",
        post_type="story",
        user_id=user.id,
        created_at=datetime(2024, 1, 2, tzinfo=timezone.utc),
    )
    db_session.add_all([post_day1, post_day2])
    db_session.commit()

    results = PostService.get_posts(
        db_session,
        sort="past",
        day=date(2024, 1, 1),
        skip=0,
        limit=10,
        post_type=None,
    )
    assert len(results) == 1
    assert results[0]["title"] == "Day One"


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
def test_adjust_post_points_updates(db_session):
    user = User(username="derek", email="derek@example.com", hashed_password=get_password_hash("Password1!"))
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    post = Post(title="Score", url=None, text="Body", post_type="story", user_id=user.id)
    db_session.add(post)
    db_session.commit()
    db_session.refresh(post)

    VoteService.vote_on_post(db_session, post.id, VoteCreate(vote_type=1), user.id)
    db_session.refresh(post)
    assert post.points == 1

