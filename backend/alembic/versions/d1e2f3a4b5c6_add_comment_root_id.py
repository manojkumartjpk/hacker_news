"""add comment root_id

Revision ID: d1e2f3a4b5c6
Revises: 8f4a1a2b3c4d
Create Date: 2026-01-06 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "d1e2f3a4b5c6"
down_revision = "8f4a1a2b3c4d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("comments", sa.Column("root_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_comments_root_id_comments",
        "comments",
        "comments",
        ["root_id"],
        ["id"],
    )
    op.create_index("ix_comments_root_id", "comments", ["root_id"])

    op.execute(
        """
        WITH RECURSIVE comment_tree AS (
            SELECT id, parent_id, id AS root_id
            FROM comments
            WHERE parent_id IS NULL
            UNION ALL
            SELECT c.id, c.parent_id, ct.root_id
            FROM comments c
            JOIN comment_tree ct ON c.parent_id = ct.id
        )
        UPDATE comments
        SET root_id = comment_tree.root_id
        FROM comment_tree
        WHERE comments.id = comment_tree.id
        """
    )


def downgrade() -> None:
    op.drop_index("ix_comments_root_id", table_name="comments")
    op.drop_constraint("fk_comments_root_id_comments", "comments", type_="foreignkey")
    op.drop_column("comments", "root_id")
