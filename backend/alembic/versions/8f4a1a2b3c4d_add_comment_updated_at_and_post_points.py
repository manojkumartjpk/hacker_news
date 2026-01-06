"""add comment updated_at and post points

Revision ID: 8f4a1a2b3c4d
Revises: c2d7b6a6f1d3
Create Date: 2026-01-06 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "8f4a1a2b3c4d"
down_revision = "c2d7b6a6f1d3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "comments",
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.alter_column("posts", "score", new_column_name="points")


def downgrade() -> None:
    op.alter_column("posts", "points", new_column_name="score")
    op.drop_column("comments", "updated_at")
