from sqlalchemy.orm import Session
from fastapi import HTTPException
from models import Comment, CommentAncestor, Post


class CommentAncestorService:
    @staticmethod
    def _load_existing_parent_ancestors(
        db: Session,
        parent_ids: set[int],
        new_comment_ids: set[int],
    ) -> dict[int, list[dict]]:
        existing_parent_ids = {pid for pid in parent_ids if pid not in new_comment_ids}
        if not existing_parent_ids:
            return {}
        rows = db.query(CommentAncestor).filter(
            CommentAncestor.descendant_comment_id.in_(existing_parent_ids)
        ).all()
        parent_map: dict[int, list[dict]] = {}
        for row in rows:
            parent_map.setdefault(row.descendant_comment_id, []).append({
                "ancestor_post_id": row.ancestor_post_id,
                "ancestor_comment_id": row.ancestor_comment_id,
                "depth": row.depth,
            })
        return parent_map

    @staticmethod
    def create_ancestors_for_comments(db: Session, comments: list[Comment]) -> None:
        if not comments:
            return
        comment_map = {comment.id: comment for comment in comments}
        new_comment_ids = set(comment_map.keys())
        parent_ids = {comment.parent_id for comment in comments if comment.parent_id}
        existing_parent_ancestors = CommentAncestorService._load_existing_parent_ancestors(
            db, parent_ids, new_comment_ids
        )
        cache: dict[int, list[dict]] = {}

        def build_rows(comment_id: int) -> list[dict]:
            if comment_id in cache:
                return cache[comment_id]
            comment = comment_map[comment_id]
            rows = [{
                "ancestor_post_id": None,
                "ancestor_comment_id": comment_id,
                "depth": 0,
            }]
            parent_id = comment.parent_id
            if parent_id is None:
                rows.append({
                    "ancestor_post_id": comment.post_id,
                    "ancestor_comment_id": None,
                    "depth": 1,
                })
            else:
                if parent_id in comment_map:
                    parent_rows = build_rows(parent_id)
                else:
                    parent_rows = existing_parent_ancestors.get(parent_id)
                if parent_rows:
                    for parent_row in parent_rows:
                        rows.append({
                            "ancestor_post_id": parent_row["ancestor_post_id"],
                            "ancestor_comment_id": parent_row["ancestor_comment_id"],
                            "depth": parent_row["depth"] + 1,
                        })
                else:
                    rows.append({
                        "ancestor_post_id": comment.post_id,
                        "ancestor_comment_id": None,
                        "depth": 1,
                    })
            cache[comment_id] = rows
            return rows

        new_rows: list[CommentAncestor] = []
        for comment_id in comment_map:
            for row in build_rows(comment_id):
                new_rows.append(CommentAncestor(
                    ancestor_post_id=row["ancestor_post_id"],
                    ancestor_comment_id=row["ancestor_comment_id"],
                    descendant_comment_id=comment_id,
                    depth=row["depth"],
                ))
        db.add_all(new_rows)

    @staticmethod
    def apply_vote_delta(db: Session, comment_id: int, delta: int) -> None:
        ancestors = db.query(
            CommentAncestor.ancestor_comment_id,
            CommentAncestor.ancestor_post_id,
        ).filter(
            CommentAncestor.descendant_comment_id == comment_id
        ).all()
        ancestor_comment_ids = {
            ancestor_comment_id
            for ancestor_comment_id, _ in ancestors
            if ancestor_comment_id and ancestor_comment_id != comment_id
        }
        ancestor_post_ids = {
            ancestor_post_id
            for _, ancestor_post_id in ancestors
            if ancestor_post_id
        }
        if ancestor_comment_ids:
            db.query(Comment).filter(
                Comment.id.in_(ancestor_comment_ids)
            ).update(
                {Comment.points: Comment.points + delta},
                synchronize_session=False,
            )
        if ancestor_post_ids:
            db.query(Post).filter(
                Post.id.in_(ancestor_post_ids)
            ).update(
                {Post.points: Post.points + delta},
                synchronize_session=False,
            )

    @staticmethod
    def backfill_for_post(db: Session, post_id: int) -> dict:
        post = db.query(Post).filter(Post.id == post_id).first()
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        comments = db.query(Comment).filter(Comment.post_id == post_id).all()
        if not comments:
            return {"post_id": post_id, "comment_count": 0, "ancestor_rows": 0}

        comment_map = {comment.id: comment.parent_id for comment in comments}
        cache: dict[int, list[dict]] = {}

        def build_rows(comment_id: int) -> list[dict]:
            if comment_id in cache:
                return cache[comment_id]
            rows = [{
                "ancestor_post_id": None,
                "ancestor_comment_id": comment_id,
                "depth": 0,
            }]
            parent_id = comment_map.get(comment_id)
            if parent_id is None or parent_id not in comment_map:
                rows.append({
                    "ancestor_post_id": post_id,
                    "ancestor_comment_id": None,
                    "depth": 1,
                })
            else:
                parent_rows = build_rows(parent_id)
                for parent_row in parent_rows:
                    rows.append({
                        "ancestor_post_id": parent_row["ancestor_post_id"],
                        "ancestor_comment_id": parent_row["ancestor_comment_id"],
                        "depth": parent_row["depth"] + 1,
                    })
            cache[comment_id] = rows
            return rows

        comment_ids = list(comment_map.keys())
        db.query(CommentAncestor).filter(
            CommentAncestor.descendant_comment_id.in_(comment_ids)
        ).delete(synchronize_session=False)

        new_rows: list[CommentAncestor] = []
        for comment_id in comment_ids:
            for row in build_rows(comment_id):
                new_rows.append(CommentAncestor(
                    ancestor_post_id=row["ancestor_post_id"],
                    ancestor_comment_id=row["ancestor_comment_id"],
                    descendant_comment_id=comment_id,
                    depth=row["depth"],
                ))
        db.add_all(new_rows)
        return {
            "post_id": post_id,
            "comment_count": len(comment_ids),
            "ancestor_rows": len(new_rows),
        }
