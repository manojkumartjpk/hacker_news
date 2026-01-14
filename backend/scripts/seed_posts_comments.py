import argparse
import os
import random
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Seed many posts with nested comments for load testing."
    )
    parser.add_argument("--posts", type=int, default=300, help="Number of posts to create.")
    parser.add_argument("--comments-per-post", type=int, default=30, help="Fixed comments per post.")
    parser.add_argument("--comments-max", type=int, default=None, help="Randomize comments per post up to this max.")
    parser.add_argument("--top-level", type=int, default=5, help="Top-level comments per post.")
    parser.add_argument("--max-depth", type=int, default=5, help="Maximum nesting depth.")
    parser.add_argument("--max-depth-random", type=int, default=None, help="Randomize nesting depth up to this max.")
    parser.add_argument("--nested-ratio", type=float, default=0.7, help="Chance a new comment nests.")
    parser.add_argument("--seed", type=int, default=11, help="Random seed for repeatability.")
    parser.add_argument("--username", default="seed_user_bulk", help="Username to own seed data.")
    parser.add_argument("--email", default="seed_user_bulk@example.com", help="Email for seed user.")
    parser.add_argument("--password", default="SeedPass1!", help="Password for seed user.")
    parser.add_argument("--title-prefix", default="Seeded post", help="Title prefix for posts.")
    parser.add_argument("--text", default="Seeded post body for load testing.", help="Post text.")
    parser.add_argument(
        "--use-queue",
        action="store_true",
        help="Use Redis write queue (disables nesting because ids are async).",
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


def choose_parent(nodes: list[dict], max_depth: int, rng: random.Random) -> dict | None:
    eligible = [node for node in nodes if node["depth"] < max_depth - 1]
    if not eligible:
        return None
    weights = [node["depth"] + 1 for node in eligible]
    return rng.choices(eligible, weights=weights, k=1)[0]


def seed_post_comments(
    db,
    post_id: int,
    user_id: int,
    rng: random.Random,
    total: int,
    max_depth: int,
) -> int:
    if total <= 0:
        return 0
    top_level = min(args.top_level, total)
    nodes: list[dict] = []

    for idx in range(top_level):
        comment = CommentService.create_comment(
            db,
            CommentCreate(text=f"Seed comment {idx + 1} (depth 0)"),
            post_id,
            user_id,
        )
        nodes.append({"id": comment["id"], "depth": 0})

    if nodes and total > len(nodes) and max_depth > 1:
        parent_id = nodes[0]["id"]
        current_depth = 1
        while len(nodes) < total and current_depth < max_depth:
            comment = CommentService.create_comment(
                db,
                CommentCreate(
                    text=f"Seed comment {len(nodes) + 1} (depth {current_depth})",
                    parent_id=parent_id,
                ),
                post_id,
                user_id,
            )
            nodes.append({"id": comment["id"], "depth": current_depth})
            parent_id = comment["id"]
            current_depth += 1

    while len(nodes) < total:
        make_nested = rng.random() < args.nested_ratio
        parent = choose_parent(nodes, max_depth, rng) if make_nested else None
        parent_id = parent["id"] if parent else None
        depth = parent["depth"] + 1 if parent else 0
        comment = CommentService.create_comment(
            db,
            CommentCreate(text=f"Seed comment {len(nodes) + 1} (depth {depth})", parent_id=parent_id),
            post_id,
            user_id,
        )
        nodes.append({"id": comment["id"], "depth": depth})

    return len(nodes)


def main() -> int:
    if args.posts <= 0:
        print("Nothing to do; post count must be positive.")
        return 1
    if args.max_depth <= 0:
        print("Invalid max depth; must be at least 1.")
        return 1

    base_rng = random.Random(args.seed)
    db = SessionLocal()
    try:
        user = get_or_create_user(db, args.username, args.email, args.password)
        total_comments = 0
        for idx in range(args.posts):
            title = f"{args.title_prefix} {idx + 1}"
            payload = PostCreate(title=title, text=args.text, post_type="story")
            try:
                post = PostService.create_post(db, payload, user.id)
            except HTTPException as exc:
                print(f"Post error: {exc.detail}")
                return 1

            rng = random.Random(base_rng.randint(1, 1_000_000))
            if args.comments_max:
                per_post = rng.randint(1, max(args.comments_max, 1))
            else:
                per_post = args.comments_per_post
            if args.max_depth_random:
                per_depth = rng.randint(1, max(args.max_depth_random, 1))
            else:
                per_depth = args.max_depth
            created = seed_post_comments(db, post["id"], user.id, rng, per_post, per_depth)
            total_comments += created
            if (idx + 1) % 25 == 0:
                print(f"Created {idx + 1} posts with {total_comments} comments...")

        print(
            "Seed complete:",
            f"posts={args.posts}",
            f"comments={total_comments}",
            f"max_depth={args.max_depth_random or args.max_depth}",
        )
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
