"""add comment points

Revision ID: b7c8d9e0f1a2
Revises: f1b2c3d4e5f6
Create Date: 2026-01-06 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "b7c8d9e0f1a2"
down_revision = "f1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "comments",
        sa.Column("points", sa.Integer(), server_default=sa.text("0"), nullable=False),
    )
    op.execute(
        sa.text(
            "UPDATE comments "
            "SET points = ("
            "SELECT COUNT(*) FROM comment_votes "
            "WHERE comment_votes.comment_id = comments.id"
            ")"
        )
    )


def downgrade() -> None:
    op.drop_column("comments", "points")
