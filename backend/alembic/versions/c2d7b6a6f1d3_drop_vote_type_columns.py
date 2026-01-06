"""drop vote_type columns

Revision ID: c2d7b6a6f1d3
Revises: 
Create Date: 2024-01-13 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = "c2d7b6a6f1d3"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("votes", "vote_type")
    op.drop_column("comment_votes", "vote_type")


def downgrade() -> None:
    op.add_column("comment_votes", sa.Column("vote_type", sa.Integer(), nullable=True))
    op.add_column("votes", sa.Column("vote_type", sa.Integer(), nullable=True))
