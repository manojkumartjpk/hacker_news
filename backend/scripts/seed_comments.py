import argparse
import os
import random
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Seed a post with nested comments for local testing."
    )
    parser.add_argument("--post-id", type=int, default=None, help="Use an existing post id.")
    parser.add_argument("--count", type=int, default=800, help="Total comments to create.")
    parser.add_argument("--top-level", type=int, default=20, help="Top-level comments to create.")
    parser.add_argument("--max-depth", type=int, default=8, help="Maximum nesting depth.")
    parser.add_argument("--nested-ratio", type=float, default=0.75, help="Chance a new comment nests.")
    parser.add_argument("--seed", type=int, default=7, help="Random seed for repeatability.")
    parser.add_argument("--username", default="seed_user", help="Username to own the seed data.")
    parser.add_argument("--email", default="seed_user@example.com", help="Email for the seed user.")
    parser.add_argument("--password", default="SeedPass1!", help="Password for the seed user.")
    parser.add_argument("--title", default="Seeded post for nested comments", help="Post title.")
    parser.add_argument("--text", default="Seeded post body for load testing comments.", help="Post text.")
    parser.add_argument(
        "--use-queue",
        action="store_true",
        help="Use the Redis write queue (disables nesting because ids are async).",
    )
    return parser.parse_args()


args = parse_args()

if args.use_queue:
    os.environ["WRITE_QUEUE_MODE"] = "redis"
    if args.max_depth > 1:
        print("Queue mode does not return ids; forcing max depth to 1 for flat comments.")
        args.max_depth = 1
        args.nested_ratio = 0.0
else:
    # Force direct writes so we get comment ids synchronously for nesting.
    os.environ["WRITE_QUEUE_MODE"] = "direct"

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from fastapi import HTTPException  # noqa: E402
from database import SessionLocal  # noqa: E402
from schemas import UserCreate, PostCreate, CommentCreate  # noqa: E402
from services import UserService, PostService, CommentService  # noqa: E402


def get_or_create_user(db, username: str, email: str, password: str):
    user = UserService.get_user_by_username(db, username=username)
    if user:
        return user
    payload = UserCreate(username=username, email=email, password=password)
    return UserService.create_user(db, payload)


def get_or_create_post(db, user_id: int, post_id: int | None) -> dict:
    if post_id is not None:
        return PostService.get_post(db, post_id)
    payload = PostCreate(title=args.title, text=args.text, post_type="story")
    return PostService.create_post(db, payload, user_id)


def choose_parent(nodes: list[dict], max_depth: int) -> dict | None:
    eligible = [node for node in nodes if node["depth"] < max_depth - 1]
    if not eligible:
        return None
    weights = [node["depth"] + 1 for node in eligible]
    return random.choices(eligible, weights=weights, k=1)[0]


def main() -> int:
    if args.count <= 0:
        print("Nothing to do; comment count must be positive.")
        return 1
    if args.max_depth <= 0:
        print("Invalid max depth; must be at least 1.")
        return 1

    random.seed(args.seed)
    db = SessionLocal()
    try:
        user = get_or_create_user(db, args.username, args.email, args.password)
        try:
            post = get_or_create_post(db, user.id, args.post_id)
        except HTTPException as exc:
            print(f"Post error: {exc.detail}")
            return 1

        total = args.count
        top_level = min(args.top_level, total)
        nodes: list[dict] = []

        for idx in range(top_level):
            comment = CommentService.create_comment(
                db,
                CommentCreate(text=f"Seed comment {idx + 1} (depth 0)"),
                post["id"],
                user.id,
            )
            nodes.append({"id": comment["id"], "depth": 0})

        # Ensure at least one deep chain for consistent nesting.
        if nodes and total > len(nodes) and args.max_depth > 1:
            parent_id = nodes[0]["id"]
            current_depth = 1
            while len(nodes) < total and current_depth < args.max_depth:
                comment = CommentService.create_comment(
                    db,
                    CommentCreate(text=f"Seed comment {len(nodes) + 1} (depth {current_depth})", parent_id=parent_id),
                    post["id"],
                    user.id,
                )
                nodes.append({"id": comment["id"], "depth": current_depth})
                parent_id = comment["id"]
                current_depth += 1

        while len(nodes) < total:
            make_nested = random.random() < args.nested_ratio
            parent = choose_parent(nodes, args.max_depth) if make_nested else None
            parent_id = parent["id"] if parent else None
            depth = parent["depth"] + 1 if parent else 0
            comment = CommentService.create_comment(
                db,
                CommentCreate(text=f"Seed comment {len(nodes) + 1} (depth {depth})", parent_id=parent_id),
                post["id"],
                user.id,
            )
            nodes.append({"id": comment["id"], "depth": depth})
            if len(nodes) % 100 == 0:
                print(f"Created {len(nodes)} comments...")

        print(
            "Seed complete:",
            f"post_id={post['id']}",
            f"comments={len(nodes)}",
            f"max_depth={args.max_depth}",
        )
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
