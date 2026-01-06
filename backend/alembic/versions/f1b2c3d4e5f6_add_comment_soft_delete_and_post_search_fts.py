"""add comment soft delete and post search fts index

Revision ID: f1b2c3d4e5f6
Revises: 8f4a1a2b3c4d
Create Date: 2026-01-07 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "f1b2c3d4e5f6"
down_revision = "d1e2f3a4b5c6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "comments",
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.false(), nullable=False),
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_posts_search_fts "
        "ON posts USING GIN (to_tsvector('english', "
        "coalesce(title, '') || ' ' || coalesce(text, '') || ' ' || coalesce(url, '')"
        "))"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_posts_search_fts")
    op.drop_column("comments", "is_deleted")
