import pytest
from fastapi import HTTPException

from auth import get_password_hash
from models import User, Notification, NotificationType, Post, Comment
from services.notification_service import NotificationService


@pytest.mark.unit
def test_mark_notification_as_read(db_session):
    user = User(username="notif", email="notif@example.com", hashed_password=get_password_hash("Password1!"))
    actor = User(username="actor", email="actor@example.com", hashed_password=get_password_hash("Password1!"))
    db_session.add_all([user, actor])
    db_session.commit()
    db_session.refresh(user)
    db_session.refresh(actor)

    post = Post(title="Post", url=None, text="Body", post_type="story", user_id=user.id)
    db_session.add(post)
    db_session.commit()
    db_session.refresh(post)

    comment = Comment(text="Comment", user_id=actor.id, post_id=post.id, parent_id=None)
    db_session.add(comment)
    db_session.commit()
    db_session.refresh(comment)

    notification = Notification(
        user_id=user.id,
        actor_id=actor.id,
        type=NotificationType.COMMENT_ON_POST,
        post_id=post.id,
        comment_id=comment.id,
        message="Hello",
    )
    db_session.add(notification)
    db_session.commit()
    db_session.refresh(notification)

    NotificationService.mark_notification_as_read(db_session, notification.id, user.id)
    assert db_session.query(Notification).first().read is True


@pytest.mark.unit
def test_mark_notification_as_read_missing(db_session):
    with pytest.raises(HTTPException):
        NotificationService.mark_notification_as_read(db_session, 999, 1)


@pytest.mark.unit
def test_get_unread_count(db_session):
    user = User(username="count", email="count@example.com", hashed_password=get_password_hash("Password1!"))
    actor = User(username="actor2", email="actor2@example.com", hashed_password=get_password_hash("Password1!"))
    db_session.add_all([user, actor])
    db_session.commit()
    db_session.refresh(user)
    db_session.refresh(actor)

    post = Post(title="Post", url=None, text="Body", post_type="story", user_id=user.id)
    db_session.add(post)
    db_session.commit()
    db_session.refresh(post)

    comment_a = Comment(text="Comment A", user_id=actor.id, post_id=post.id, parent_id=None)
    comment_b = Comment(text="Comment B", user_id=actor.id, post_id=post.id, parent_id=None)
    db_session.add_all([comment_a, comment_b])
    db_session.commit()
    db_session.refresh(comment_a)
    db_session.refresh(comment_b)

    unread = Notification(
        user_id=user.id,
        actor_id=actor.id,
        type=NotificationType.REPLY_TO_COMMENT,
        post_id=post.id,
        comment_id=comment_a.id,
        message="Unread",
        read=False,
    )
    read = Notification(
        user_id=user.id,
        actor_id=actor.id,
        type=NotificationType.REPLY_TO_COMMENT,
        post_id=post.id,
        comment_id=comment_b.id,
        message="Read",
        read=True,
    )
    db_session.add_all([unread, read])
    db_session.commit()

    assert NotificationService.get_unread_count(db_session, user.id) == 1
