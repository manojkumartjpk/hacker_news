import argparse
import asyncio
import random
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate peak activity traffic and report write success rates."
    )
    parser.add_argument("--base-url", default="http://localhost:8000", help="API base URL.")
    parser.add_argument("--users", type=int, default=50, help="Number of users to simulate.")
    parser.add_argument("--duration-seconds", type=int, default=30, help="Test duration.")
    parser.add_argument("--sleep-ms", type=int, default=0, help="Sleep between actions per user.")
    parser.add_argument("--post-sample", type=int, default=300, help="Max posts to sample.")
    parser.add_argument("--comment-sample", type=int, default=2000, help="Max comments to sample.")
    parser.add_argument("--comment-weight", type=int, default=4, help="Weight for add-comment actions.")
    parser.add_argument("--post-vote-weight", type=int, default=3, help="Weight for post vote actions.")
    parser.add_argument("--comment-vote-weight", type=int, default=3, help="Weight for comment vote actions.")
    parser.add_argument("--reply-ratio", type=float, default=0.6, help="Chance a comment is a reply.")
    parser.add_argument("--wait-seconds", type=int, default=10, help="Wait for async writes to settle.")
    parser.add_argument("--timeout-seconds", type=float, default=10.0, help="HTTP timeout per request.")
    parser.add_argument("--seed", type=int, default=23, help="Random seed.")
    parser.add_argument("--username-prefix", default="load_user", help="Username prefix.")
    return parser.parse_args()


args = parse_args()

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from database import SessionLocal  # noqa: E402
from models import Comment, Post, User, Vote, CommentVote  # noqa: E402
from schemas import UserCreate  # noqa: E402
from services import UserService  # noqa: E402
from auth import create_access_token  # noqa: E402


@dataclass
class Stats:
    total: int = 0
    ok_200: int = 0
    ok_202: int = 0
    errors: int = 0
    status_counts: dict[int, int] = field(default_factory=dict)
    comment_add_ok: int = 0
    post_vote_add_ok: int = 0
    post_vote_remove_ok: int = 0
    comment_vote_add_ok: int = 0
    comment_vote_remove_ok: int = 0
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    async def record(self, status_code: int, action: str | None = None) -> None:
        async with self.lock:
            self.total += 1
            self.status_counts[status_code] = self.status_counts.get(status_code, 0) + 1
            if status_code == 200:
                self.ok_200 += 1
            elif status_code == 202:
                self.ok_202 += 1
            else:
                self.errors += 1
            if action == "comment_add":
                self.comment_add_ok += 1
            elif action == "post_vote_add":
                self.post_vote_add_ok += 1
            elif action == "post_vote_remove":
                self.post_vote_remove_ok += 1
            elif action == "comment_vote_add":
                self.comment_vote_add_ok += 1
            elif action == "comment_vote_remove":
                self.comment_vote_remove_ok += 1


def get_or_create_user(db, username: str) -> User:
    existing = UserService.get_user_by_username(db, username=username)
    if existing:
        return existing
    payload = UserCreate(username=username, email=f"{username}@example.com", password="LoadPass1!")
    return UserService.create_user(db, payload)


def load_ids(db) -> tuple[list[int], dict[int, list[int]]]:
    post_ids = [row[0] for row in db.query(Post.id).limit(args.post_sample).all()]
    comment_rows = db.query(Comment.id, Comment.post_id).limit(args.comment_sample).all()
    comments_by_post: dict[int, list[int]] = {}
    for comment_id, post_id in comment_rows:
        comments_by_post.setdefault(post_id, []).append(comment_id)
    return post_ids, comments_by_post


async def request_with_auth(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    token: str,
    json_payload: dict | None = None,
) -> int:
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = await client.request(method, url, json=json_payload, headers=headers)
        return response.status_code
    except httpx.RequestError:
        return 0


async def user_loop(
    client: httpx.AsyncClient,
    token: str,
    post_ids: list[int],
    comments_by_post: dict[int, list[int]],
    end_time: float,
    rng: random.Random,
    stats: Stats,
) -> None:
    voted_posts: set[int] = set()
    voted_comments: set[int] = set()
    action_weights = [
        ("comment", args.comment_weight),
        ("post_vote", args.post_vote_weight),
        ("comment_vote", args.comment_vote_weight),
    ]
    sleep_seconds = args.sleep_ms / 1000.0

    while asyncio.get_event_loop().time() < end_time:
        action = rng.choices(
            [item[0] for item in action_weights],
            weights=[item[1] for item in action_weights],
            k=1,
        )[0]

        if action == "comment":
            post_id = rng.choice(post_ids)
            parent_id = None
            if comments_by_post.get(post_id) and rng.random() < args.reply_ratio:
                parent_id = rng.choice(comments_by_post[post_id])
            payload = {"text": f"Load test comment {rng.randint(1, 1_000_000)}"}
            if parent_id is not None:
                payload["parent_id"] = parent_id
            status = await request_with_auth(
                client,
                "POST",
                f"{args.base_url}/posts/{post_id}/comments",
                token,
                payload,
            )
            if status in {200, 202}:
                await stats.record(status, action="comment_add")
            else:
                await stats.record(status)

        elif action == "post_vote":
            post_id = rng.choice(post_ids)
            if post_id in voted_posts:
                status = await request_with_auth(
                    client,
                    "DELETE",
                    f"{args.base_url}/posts/{post_id}/vote",
                    token,
                )
                if status in {200, 202}:
                    voted_posts.discard(post_id)
                    await stats.record(status, action="post_vote_remove")
                else:
                    await stats.record(status)
            else:
                status = await request_with_auth(
                    client,
                    "POST",
                    f"{args.base_url}/posts/{post_id}/vote",
                    token,
                    {"vote_type": 1},
                )
                if status in {200, 202}:
                    voted_posts.add(post_id)
                    await stats.record(status, action="post_vote_add")
                else:
                    await stats.record(status)

        else:
            post_id = rng.choice(post_ids)
            comment_ids = comments_by_post.get(post_id, [])
            if not comment_ids:
                if sleep_seconds:
                    await asyncio.sleep(sleep_seconds)
                continue
            comment_id = rng.choice(comment_ids)
            if comment_id in voted_comments:
                status = await request_with_auth(
                    client,
                    "DELETE",
                    f"{args.base_url}/comment_votes/{comment_id}/vote",
                    token,
                )
                if status in {200, 202}:
                    voted_comments.discard(comment_id)
                    await stats.record(status, action="comment_vote_remove")
                else:
                    await stats.record(status)
            else:
                status = await request_with_auth(
                    client,
                    "POST",
                    f"{args.base_url}/comment_votes/{comment_id}/vote",
                    token,
                    {"vote_type": 1},
                )
                if status in {200, 202}:
                    voted_comments.add(comment_id)
                    await stats.record(status, action="comment_vote_add")
                else:
                    await stats.record(status)

        if sleep_seconds:
            await asyncio.sleep(sleep_seconds)


async def run_load_test(tokens: list[str], post_ids: list[int], comments_by_post: dict[int, list[int]]) -> Stats:
    stats = Stats()
    timeout = httpx.Timeout(args.timeout_seconds, connect=5.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        rng = random.Random(args.seed)
        start = asyncio.get_event_loop().time()
        end_time = start + args.duration_seconds
        tasks = []
        for idx, token in enumerate(tokens):
            user_rng = random.Random(rng.randint(1, 1_000_000) + idx)
            tasks.append(
                asyncio.create_task(
                    user_loop(client, token, post_ids, comments_by_post, end_time, user_rng, stats)
                )
            )
        await asyncio.gather(*tasks)
    return stats


def main() -> int:
    if args.users <= 0:
        print("User count must be positive.")
        return 1

    db = SessionLocal()
    try:
        post_ids, comments_by_post = load_ids(db)
        if not post_ids:
            print("No posts found. Seed posts before running this test.")
            return 1
        if not comments_by_post:
            print("No comments found. Seed comments before running this test.")
            return 1

        users: list[User] = []
        tokens: list[str] = []
        for idx in range(args.users):
            username = f"{args.username_prefix}_{idx + 1}"
            user = get_or_create_user(db, username)
            users.append(user)
            tokens.append(create_access_token({"sub": user.username}))

        start_time = datetime.now(timezone.utc)
        stats = asyncio.run(run_load_test(tokens, post_ids, comments_by_post))
        if args.wait_seconds:
            asyncio.run(asyncio.sleep(args.wait_seconds))
        end_time = datetime.now(timezone.utc)

        user_ids = [user.id for user in users]
        comment_count = (
            db.query(Comment)
            .filter(Comment.user_id.in_(user_ids))
            .filter(Comment.created_at >= start_time, Comment.created_at <= end_time)
            .count()
        )
        post_vote_count = (
            db.query(Vote)
            .filter(Vote.user_id.in_(user_ids))
            .filter(Vote.created_at >= start_time, Vote.created_at <= end_time)
            .count()
        )
        comment_vote_count = (
            db.query(CommentVote)
            .filter(CommentVote.user_id.in_(user_ids))
            .filter(CommentVote.created_at >= start_time, CommentVote.created_at <= end_time)
            .count()
        )

        duration = max(args.duration_seconds, 1)
        rps = stats.total / duration
        print("Load test complete.")
        print(f"Requests: total={stats.total} ok_200={stats.ok_200} ok_202={stats.ok_202} errors={stats.errors}")
        print(f"RPS: {rps:.2f} over {duration}s with users={args.users}")
        print(f"Status codes: {stats.status_counts}")
        print(
            "Writes vs DB rows:",
            f"comments_ok={stats.comment_add_ok} db_comments={comment_count}",
            f"post_vote_add_ok={stats.post_vote_add_ok} db_post_votes={post_vote_count}",
            f"comment_vote_add_ok={stats.comment_vote_add_ok} db_comment_votes={comment_vote_count}",
        )
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
