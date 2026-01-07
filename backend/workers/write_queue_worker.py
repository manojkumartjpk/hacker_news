import os
import socket
import time
import logging
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import redis
from sqlalchemy import delete, func, select, tuple_, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.exc import IntegrityError

from cache import REDIS_ENABLED, redis_client, redis_incr
from database import SessionLocal
from models import (
    Comment,
    CommentVote,
    Notification,
    NotificationType,
    Post,
    QueuedWrite,
    User,
    Vote,
)
from services.comment_service import CommentService
from services.queue_service import WRITE_STREAM_KEY, WriteEventType


LOGGER = logging.getLogger("write_queue_worker")
logging.basicConfig(level=logging.INFO)

WRITE_STREAM_GROUP = os.getenv("WRITE_STREAM_GROUP", "hn-write-workers")
WRITE_STREAM_CONSUMER = os.getenv("WRITE_STREAM_CONSUMER", socket.gethostname())
WRITE_BATCH_SIZE = int(os.getenv("WRITE_BATCH_SIZE", "200"))
WRITE_BLOCK_MS = int(os.getenv("WRITE_BLOCK_MS", "5000"))
FEED_REFRESH_SECONDS = int(os.getenv("FEED_REFRESH_SECONDS", "60"))


def _ensure_consumer_group() -> None:
    if not REDIS_ENABLED or redis_client is None:
        raise RuntimeError("Redis is not available")
    try:
        redis_client.xgroup_create(WRITE_STREAM_KEY, WRITE_STREAM_GROUP, id="0", mkstream=True)
    except redis.ResponseError as exc:
        if "BUSYGROUP" not in str(exc):
            raise


def _claim_request_ids(db, events: list[dict]) -> set[str]:
    if not events:
        return set()
    values = [
        {"request_id": event["request_id"], "event_type": event["type"]}
        for event in events
        if event.get("request_id")
    ]
    if not values:
        return set()

    dialect = db.bind.dialect.name if db.bind else "unknown"
    if dialect == "postgresql":
        stmt = (
            pg_insert(QueuedWrite)
            .values(values)
            .on_conflict_do_nothing(index_elements=["request_id"])
            .returning(QueuedWrite.request_id)
        )
        rows = db.execute(stmt).scalars().all()
        return set(rows)

    accepted: set[str] = set()
    for payload in values:
        try:
            with db.begin_nested():
                db.add(QueuedWrite(**payload))
                db.flush()
                accepted.add(payload["request_id"])
        except IntegrityError:
            continue
    return accepted


def _create_notifications(db, comment: Comment) -> None:
    post = db.query(Post).filter(Post.id == comment.post_id).first()
    actor = db.query(User).filter(User.id == comment.user_id).first()
    if not post or not actor:
        return

    if comment.user_id != post.user_id:
        db.add(Notification(
            user_id=post.user_id,
            actor_id=comment.user_id,
            type=NotificationType.COMMENT_ON_POST,
            post_id=post.id,
            comment_id=comment.id,
            message=f"{actor.username} commented on your post '{post.title}'",
        ))

    if comment.parent_id:
        parent_comment = db.query(Comment).filter(Comment.id == comment.parent_id).first()
        if not parent_comment:
            return
        if comment.user_id != parent_comment.user_id:
            db.add(Notification(
                user_id=parent_comment.user_id,
                actor_id=comment.user_id,
                type=NotificationType.REPLY_TO_COMMENT,
                post_id=post.id,
                comment_id=comment.id,
                message=f"{actor.username} replied to your comment",
            ))


def _refresh_post_points(db, post_ids: set[int]) -> None:
    if not post_ids:
        return
    ids = list(post_ids)
    subq = (
        select(Vote.post_id, func.count(Vote.id).label("cnt"))
        .where(Vote.post_id.in_(ids))
        .group_by(Vote.post_id)
        .subquery()
    )
    db.execute(update(Post).where(Post.id.in_(ids)).values(points=0))
    db.execute(
        update(Post)
        .where(Post.id == subq.c.post_id)
        .values(points=subq.c.cnt)
    )


def _refresh_comment_points(db, comment_ids: set[int]) -> None:
    if not comment_ids:
        return
    ids = list(comment_ids)
    subq = (
        select(CommentVote.comment_id, func.count(CommentVote.id).label("cnt"))
        .where(CommentVote.comment_id.in_(ids))
        .group_by(CommentVote.comment_id)
        .subquery()
    )
    db.execute(update(Comment).where(Comment.id.in_(ids)).values(points=0))
    db.execute(
        update(Comment)
        .where(Comment.id == subq.c.comment_id)
        .values(points=subq.c.cnt)
    )


def _split_events(events: list[dict]) -> dict[str, list[dict]]:
    return {
        WriteEventType.COMMENT_ADD: [e for e in events if e["type"] == WriteEventType.COMMENT_ADD],
        WriteEventType.COMMENT_DELETE: [e for e in events if e["type"] == WriteEventType.COMMENT_DELETE],
        WriteEventType.POST_VOTE_ADD: [e for e in events if e["type"] == WriteEventType.POST_VOTE_ADD],
        WriteEventType.POST_VOTE_REMOVE: [e for e in events if e["type"] == WriteEventType.POST_VOTE_REMOVE],
        WriteEventType.COMMENT_VOTE_ADD: [e for e in events if e["type"] == WriteEventType.COMMENT_VOTE_ADD],
        WriteEventType.COMMENT_VOTE_REMOVE: [e for e in events if e["type"] == WriteEventType.COMMENT_VOTE_REMOVE],
    }


def _fetch_valid_post_ids(db, post_ids: set[int]) -> set[int]:
    if not post_ids:
        return set()
    rows = db.execute(select(Post.id).where(Post.id.in_(post_ids))).all()
    return {row[0] for row in rows}


def _fetch_valid_comment_ids(db, comment_ids: set[int]) -> set[int]:
    if not comment_ids:
        return set()
    rows = db.execute(select(Comment.id).where(Comment.id.in_(comment_ids))).all()
    return {row[0] for row in rows}


def _load_parent_map(db, parent_ids: set[int]) -> dict[int, dict]:
    if not parent_ids:
        return {}
    rows = db.execute(
        select(Comment.id, Comment.post_id, Comment.root_id).where(Comment.id.in_(parent_ids))
    ).all()
    return {row[0]: {"post_id": row[1], "root_id": row[2]} for row in rows}


def _apply_comment_adds(
    db,
    events: list[dict],
    valid_posts: set[int],
    parent_map: dict[int, dict],
) -> set[int]:
    created_comments: list[Comment] = []
    for event in events:
        post_id = int(event.get("post_id") or 0)
        if post_id not in valid_posts:
            continue
        parent_id = int(event["parent_id"]) if event.get("parent_id") else None
        root_id = None
        if parent_id:
            parent = parent_map.get(parent_id)
            if not parent or parent["post_id"] != post_id:
                continue
            root_id = parent["root_id"] or parent_id

        new_comment = Comment(
            text=event.get("text") or "",
            user_id=int(event.get("user_id") or 0),
            post_id=post_id,
            parent_id=parent_id,
            root_id=root_id,
        )
        db.add(new_comment)
        created_comments.append(new_comment)

    comment_cache_bumps: set[int] = set()
    if created_comments:
        db.flush()
        for comment in created_comments:
            if comment.parent_id is None:
                comment.root_id = comment.id
            _create_notifications(db, comment)
            comment_cache_bumps.add(comment.post_id)
    return comment_cache_bumps


def _apply_comment_deletes(db, events: list[dict]) -> set[int]:
    comment_ids = {int(e["comment_id"]) for e in events if e.get("comment_id")}
    if not comment_ids:
        return set()
    rows = db.execute(select(Comment).where(Comment.id.in_(comment_ids))).scalars().all()
    comment_map = {comment.id: comment for comment in rows}
    comment_cache_bumps: set[int] = set()
    for event in events:
        comment_id = int(event.get("comment_id") or 0)
        comment = comment_map.get(comment_id)
        if not comment:
            continue
        if int(event.get("user_id") or 0) != comment.user_id:
            continue
        if comment.is_deleted:
            continue
        comment.is_deleted = True
        comment.text = "[deleted]"
        comment_cache_bumps.add(comment.post_id)
    return comment_cache_bumps


def _apply_post_vote_adds(db, events: list[dict], valid_posts: set[int]) -> set[int]:
    pairs = {
        (int(e.get("user_id") or 0), int(e.get("post_id") or 0))
        for e in events
        if int(e.get("post_id") or 0) in valid_posts
    }
    if not pairs:
        return set()
    stmt = (
        pg_insert(Vote)
        .values([{"user_id": u, "post_id": p} for u, p in pairs])
        .on_conflict_do_nothing(index_elements=["user_id", "post_id"])
        if db.bind.dialect.name == "postgresql"
        else sqlite_insert(Vote).values([{"user_id": u, "post_id": p} for u, p in pairs]).prefix_with("OR IGNORE")
    )
    db.execute(stmt)
    return {p for _, p in pairs}


def _apply_post_vote_removes(db, events: list[dict], valid_posts: set[int]) -> set[int]:
    pairs = {
        (int(e.get("user_id") or 0), int(e.get("post_id") or 0))
        for e in events
        if int(e.get("post_id") or 0) in valid_posts
    }
    if not pairs:
        return set()
    db.execute(delete(Vote).where(tuple_(Vote.user_id, Vote.post_id).in_(pairs)))
    return {p for _, p in pairs}


def _apply_comment_vote_adds(db, events: list[dict], valid_comments: set[int]) -> set[int]:
    pairs = {
        (int(e.get("user_id") or 0), int(e.get("comment_id") or 0))
        for e in events
        if int(e.get("comment_id") or 0) in valid_comments
    }
    if not pairs:
        return set()
    stmt = (
        pg_insert(CommentVote)
        .values([{"user_id": u, "comment_id": c} for u, c in pairs])
        .on_conflict_do_nothing(index_elements=["user_id", "comment_id"])
        if db.bind.dialect.name == "postgresql"
        else sqlite_insert(CommentVote).values([{"user_id": u, "comment_id": c} for u, c in pairs]).prefix_with("OR IGNORE")
    )
    db.execute(stmt)
    return {c for _, c in pairs}


def _apply_comment_vote_removes(db, events: list[dict], valid_comments: set[int]) -> set[int]:
    pairs = {
        (int(e.get("user_id") or 0), int(e.get("comment_id") or 0))
        for e in events
        if int(e.get("comment_id") or 0) in valid_comments
    }
    if not pairs:
        return set()
    db.execute(delete(CommentVote).where(tuple_(CommentVote.user_id, CommentVote.comment_id).in_(pairs)))
    return {c for _, c in pairs}


def _process_events(events: list[dict]) -> bool:
    if not events:
        return True

    comment_cache_bumps: set[int] = set()
    post_point_ids: set[int] = set()
    comment_point_ids: set[int] = set()

    with SessionLocal() as db:
        try:
            with db.begin():
                accepted = _claim_request_ids(db, events)
                actionable = [event for event in events if event.get("request_id") in accepted]
                if not actionable:
                    return True

                buckets = _split_events(actionable)

                if buckets[WriteEventType.COMMENT_ADD]:
                    post_ids = {int(e["post_id"]) for e in buckets[WriteEventType.COMMENT_ADD] if e.get("post_id")}
                    parent_ids = {int(e["parent_id"]) for e in buckets[WriteEventType.COMMENT_ADD] if e.get("parent_id")}
                    valid_posts = _fetch_valid_post_ids(db, post_ids)
                    parent_map = _load_parent_map(db, parent_ids)
                    comment_cache_bumps.update(
                        _apply_comment_adds(db, buckets[WriteEventType.COMMENT_ADD], valid_posts, parent_map)
                    )

                if buckets[WriteEventType.COMMENT_DELETE]:
                    comment_cache_bumps.update(_apply_comment_deletes(db, buckets[WriteEventType.COMMENT_DELETE]))

                if buckets[WriteEventType.POST_VOTE_ADD]:
                    post_ids = {int(e.get("post_id") or 0) for e in buckets[WriteEventType.POST_VOTE_ADD]}
                    valid_posts = _fetch_valid_post_ids(db, post_ids)
                    post_point_ids.update(
                        _apply_post_vote_adds(db, buckets[WriteEventType.POST_VOTE_ADD], valid_posts)
                    )

                if buckets[WriteEventType.POST_VOTE_REMOVE]:
                    post_ids = {int(e.get("post_id") or 0) for e in buckets[WriteEventType.POST_VOTE_REMOVE]}
                    valid_posts = _fetch_valid_post_ids(db, post_ids)
                    post_point_ids.update(
                        _apply_post_vote_removes(db, buckets[WriteEventType.POST_VOTE_REMOVE], valid_posts)
                    )

                if buckets[WriteEventType.COMMENT_VOTE_ADD]:
                    comment_ids = {int(e.get("comment_id") or 0) for e in buckets[WriteEventType.COMMENT_VOTE_ADD]}
                    valid_comments = _fetch_valid_comment_ids(db, comment_ids)
                    comment_point_ids.update(
                        _apply_comment_vote_adds(db, buckets[WriteEventType.COMMENT_VOTE_ADD], valid_comments)
                    )

                if buckets[WriteEventType.COMMENT_VOTE_REMOVE]:
                    comment_ids = {int(e.get("comment_id") or 0) for e in buckets[WriteEventType.COMMENT_VOTE_REMOVE]}
                    valid_comments = _fetch_valid_comment_ids(db, comment_ids)
                    comment_point_ids.update(
                        _apply_comment_vote_removes(db, buckets[WriteEventType.COMMENT_VOTE_REMOVE], valid_comments)
                    )

                _refresh_post_points(db, post_point_ids)
                _refresh_comment_points(db, comment_point_ids)
        except Exception:
            LOGGER.exception("Failed processing write events batch")
            return False

    for post_id in comment_cache_bumps:
        CommentService.bump_comments_cache_version(post_id)

    return True


def run_worker() -> None:
    _ensure_consumer_group()
    last_feed_bump = time.monotonic()
    LOGGER.info("Write queue worker started")
    while True:
        if time.monotonic() - last_feed_bump >= FEED_REFRESH_SECONDS:
            redis_incr("feed:version")
            last_feed_bump = time.monotonic()

        response = redis_client.xreadgroup(
            WRITE_STREAM_GROUP,
            WRITE_STREAM_CONSUMER,
            {WRITE_STREAM_KEY: ">"},
            count=WRITE_BATCH_SIZE,
            block=WRITE_BLOCK_MS,
        )
        if not response:
            continue

        message_ids = []
        events = []
        for _, messages in response:
            for message_id, fields in messages:
                message_ids.append(message_id)
                events.append(fields | {"id": message_id})

        if _process_events(events):
            redis_client.xack(WRITE_STREAM_KEY, WRITE_STREAM_GROUP, *message_ids)


if __name__ == "__main__":
    run_worker()
