import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from auth import get_password_hash
from models import User, Post, Comment, Notification
from schemas import CommentCreate, CommentUpdate
import services.comment_service as comment_service
from services.comment_service import CommentService


@pytest.mark.unit
def test_create_comment_rejects_missing_parent(db_session):
    user = User(username="dana", email="dana@example.com", hashed_password=get_password_hash("Password1!"))
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    post = Post(title="Post", url=None, text="Body", post_type="story", user_id=user.id)
    db_session.add(post)
    db_session.commit()
    db_session.refresh(post)

    with pytest.raises(HTTPException) as exc:
        CommentService.create_comment(
            db_session,
            CommentCreate(text="Reply", parent_id=999),
            post.id,
            user.id,
        )
    assert exc.value.status_code == 404


@pytest.mark.unit
def test_create_comment_rejects_parent_mismatch(db_session):
    user = User(username="erin", email="erin@example.com", hashed_password=get_password_hash("Password1!"))
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    post_a = Post(title="Post A", url=None, text="Body", post_type="story", user_id=user.id)
    post_b = Post(title="Post B", url=None, text="Body", post_type="story", user_id=user.id)
    db_session.add_all([post_a, post_b])
    db_session.commit()
    db_session.refresh(post_a)
    db_session.refresh(post_b)

    parent = Comment(text="Parent", user_id=user.id, post_id=post_a.id, parent_id=None)
    db_session.add(parent)
    db_session.commit()
    db_session.refresh(parent)

    with pytest.raises(HTTPException) as exc:
        CommentService.create_comment(
            db_session,
            CommentCreate(text="Bad child", parent_id=parent.id),
            post_b.id,
            user.id,
        )
    assert exc.value.status_code == 400


@pytest.mark.unit
def test_create_comment_rejects_empty_text(db_session):
    user = User(username="empty", email="empty@example.com", hashed_password=get_password_hash("Password1!"))
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    post = Post(title="Post", url=None, text="Body", post_type="story", user_id=user.id)
    db_session.add(post)
    db_session.commit()
    db_session.refresh(post)

    with pytest.raises(ValidationError):
        CommentCreate(text="   ", parent_id=None)


@pytest.mark.unit
def test_create_comment_rejects_missing_post(db_session):
    user = User(username="nopost", email="nopost@example.com", hashed_password=get_password_hash("Password1!"))
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    with pytest.raises(HTTPException) as exc:
        CommentService.create_comment(db_session, CommentCreate(text="Hi", parent_id=None), 999, user.id)
    assert exc.value.status_code == 404


@pytest.mark.unit
def test_get_comment_missing(db_session):
    with pytest.raises(HTTPException):
        CommentService.get_comment(db_session, 999)


@pytest.mark.unit
def test_get_comments_for_post_missing(db_session):
    with pytest.raises(HTTPException):
        CommentService.get_comments_for_post(db_session, 999)


@pytest.mark.unit
def test_update_comment_unauthorized(db_session):
    author = User(username="owner", email="owner@example.com", hashed_password=get_password_hash("Password1!"))
    other = User(username="other", email="other@example.com", hashed_password=get_password_hash("Password1!"))
    db_session.add_all([author, other])
    db_session.commit()
    db_session.refresh(author)
    db_session.refresh(other)

    post = Post(title="Post", url=None, text="Body", post_type="story", user_id=author.id)
    db_session.add(post)
    db_session.commit()
    db_session.refresh(post)

    comment = Comment(text="Original", user_id=author.id, post_id=post.id, parent_id=None)
    db_session.add(comment)
    db_session.commit()
    db_session.refresh(comment)

    with pytest.raises(HTTPException) as exc:
        CommentService.update_comment(db_session, comment.id, CommentUpdate(text="Nope"), other.id)
    assert exc.value.status_code == 403


@pytest.mark.unit
def test_update_comment_success(db_session):
    author = User(username="updater", email="updater@example.com", hashed_password=get_password_hash("Password1!"))
    db_session.add(author)
    db_session.commit()
    db_session.refresh(author)

    post = Post(title="Post", url=None, text="Body", post_type="story", user_id=author.id)
    db_session.add(post)
    db_session.commit()
    db_session.refresh(post)

    comment = Comment(text="Original", user_id=author.id, post_id=post.id, parent_id=None)
    db_session.add(comment)
    db_session.commit()
    db_session.refresh(comment)

    updated = CommentService.update_comment(db_session, comment.id, CommentUpdate(text="Updated"), author.id)
    assert updated["text"] == "Updated"
    assert updated["username"] == author.username


@pytest.mark.unit
def test_delete_comment_unauthorized(db_session):
    author = User(username="owner2", email="owner2@example.com", hashed_password=get_password_hash("Password1!"))
    other = User(username="other2", email="other2@example.com", hashed_password=get_password_hash("Password1!"))
    db_session.add_all([author, other])
    db_session.commit()
    db_session.refresh(author)
    db_session.refresh(other)

    post = Post(title="Post", url=None, text="Body", post_type="story", user_id=author.id)
    db_session.add(post)
    db_session.commit()
    db_session.refresh(post)

    comment = Comment(text="Original", user_id=author.id, post_id=post.id, parent_id=None)
    db_session.add(comment)
    db_session.commit()
    db_session.refresh(comment)

    with pytest.raises(HTTPException) as exc:
        CommentService.delete_comment(db_session, comment.id, other.id)
    assert exc.value.status_code == 403


@pytest.mark.unit
def test_create_comment_on_own_post_no_notification(db_session):
    user = User(username="self", email="self@example.com", hashed_password=get_password_hash("Password1!"))
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    post = Post(title="Post", url=None, text="Body", post_type="story", user_id=user.id)
    db_session.add(post)
    db_session.commit()
    db_session.refresh(post)

    CommentService.create_comment(db_session, CommentCreate(text="Self", parent_id=None), post.id, user.id)
    notifications = db_session.query(Notification).filter(Notification.user_id == user.id).all()
    assert notifications == []


@pytest.mark.unit
def test_reply_creates_parent_notification(db_session):
    author = User(username="parent", email="parent@example.com", hashed_password=get_password_hash("Password1!"))
    replier = User(username="replier", email="replier@example.com", hashed_password=get_password_hash("Password1!"))
    db_session.add_all([author, replier])
    db_session.commit()
    db_session.refresh(author)
    db_session.refresh(replier)

    post = Post(title="Post", url=None, text="Body", post_type="story", user_id=author.id)
    db_session.add(post)
    db_session.commit()
    db_session.refresh(post)

    parent_comment = Comment(text="Parent", user_id=author.id, post_id=post.id, parent_id=None)
    db_session.add(parent_comment)
    db_session.commit()
    db_session.refresh(parent_comment)

    CommentService.create_comment(
        db_session,
        CommentCreate(text="Reply", parent_id=parent_comment.id),
        post.id,
        replier.id,
    )
    notifications = db_session.query(Notification).filter(Notification.user_id == author.id).all()
    assert len(notifications) == 2


@pytest.mark.unit
def test_create_notification_for_comment_handles_missing_entities(db_session):
    user = User(username="actor", email="actor@example.com", hashed_password=get_password_hash("Password1!"))
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    comment = Comment(text="Orphan", user_id=user.id, post_id=999, parent_id=None)
    CommentService._create_notification_for_comment(db_session, comment)

    post = Post(title="Post", url=None, text="Body", post_type="story", user_id=user.id)
    db_session.add(post)
    db_session.commit()
    db_session.refresh(post)

    comment_with_missing_parent = Comment(text="Child", user_id=user.id, post_id=post.id, parent_id=888)
    CommentService._create_notification_for_comment(db_session, comment_with_missing_parent)


@pytest.mark.unit
def test_delete_comment_keeps_notifications(db_session):
    author = User(username="fiona", email="fiona@example.com", hashed_password=get_password_hash("Password1!"))
    commenter = User(username="gary", email="gary@example.com", hashed_password=get_password_hash("Password1!"))
    db_session.add_all([author, commenter])
    db_session.commit()
    db_session.refresh(author)
    db_session.refresh(commenter)

    post = Post(title="Post", url=None, text="Body", post_type="story", user_id=author.id)
    db_session.add(post)
    db_session.commit()
    db_session.refresh(post)

    comment = CommentService.create_comment(
        db_session,
        CommentCreate(text="Hi", parent_id=None),
        post.id,
        commenter.id,
    )

    notifications = db_session.query(Notification).filter(Notification.user_id == author.id).all()
    assert len(notifications) == 1

    CommentService.delete_comment(db_session, comment["id"], commenter.id)
    notifications_after = db_session.query(Notification).filter(Notification.user_id == author.id).all()
    assert len(notifications_after) == 1


@pytest.mark.unit
def test_get_comments_for_post_uses_cache(db_session):
    user = User(username="cache-comment", email="cache-comment@example.com", hashed_password=get_password_hash("Password1!"))
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    post = Post(title="Cache Post", url=None, text="Body", post_type="story", user_id=user.id)
    db_session.add(post)
    db_session.commit()
    db_session.refresh(post)

    first_comment = Comment(text="First cached", user_id=user.id, post_id=post.id, parent_id=None)
    db_session.add(first_comment)
    db_session.commit()

    initial = CommentService.get_comments_for_post(db_session, post.id)
    assert len(initial) == 1

    second_comment = Comment(text="Second uncached", user_id=user.id, post_id=post.id, parent_id=None)
    db_session.add(second_comment)
    db_session.commit()

    cached = CommentService.get_comments_for_post(db_session, post.id)
    assert len(cached) == 1
    assert cached[0]["text"] == "First cached"


@pytest.mark.unit
def test_create_comment_queued_when_queue_enabled(db_session, monkeypatch):
    user = User(username="queued", email="queued@example.com", hashed_password=get_password_hash("Password1!"))
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    post = Post(title="Queued Post", url=None, text="Body", post_type="story", user_id=user.id)
    db_session.add(post)
    db_session.commit()
    db_session.refresh(post)

    monkeypatch.setattr(comment_service, "queue_writes_enabled", lambda: True)
    monkeypatch.setattr(comment_service, "enqueue_write", lambda *args, **kwargs: "req-1")

    result = CommentService.create_comment(
        db_session,
        CommentCreate(text="Queued comment", parent_id=None),
        post.id,
        user.id,
    )

    assert result["status"] == "queued"
    assert result["request_id"] == "req-1"
    assert db_session.query(Comment).count() == 0


@pytest.mark.unit
def test_delete_comment_queued_when_queue_enabled(db_session, monkeypatch):
    user = User(username="queued-del", email="queued-del@example.com", hashed_password=get_password_hash("Password1!"))
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    post = Post(title="Queued Delete", url=None, text="Body", post_type="story", user_id=user.id)
    db_session.add(post)
    db_session.commit()
    db_session.refresh(post)

    comment = Comment(text="To delete", user_id=user.id, post_id=post.id, parent_id=None)
    db_session.add(comment)
    db_session.commit()
    db_session.refresh(comment)

    monkeypatch.setattr(comment_service, "queue_writes_enabled", lambda: True)
    monkeypatch.setattr(comment_service, "enqueue_write", lambda *args, **kwargs: "req-2")

    result = CommentService.delete_comment(db_session, comment.id, user.id)
    db_session.refresh(comment)

    assert result["status"] == "queued"
    assert result["request_id"] == "req-2"
    assert comment.is_deleted is False
