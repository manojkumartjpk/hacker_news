"""add queued write requests

Revision ID: e3f4a5b6c7d8
Revises: b7c8d9e0f1a2
Create Date: 2026-01-06 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "e3f4a5b6c7d8"
down_revision = "b7c8d9e0f1a2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "queued_write_requests" in inspector.get_table_names():
        return
    op.create_table(
        "queued_write_requests",
        sa.Column("request_id", sa.String(length=64), primary_key=True),
        sa.Column("event_type", sa.String(length=50), nullable=False, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("queued_write_requests")
