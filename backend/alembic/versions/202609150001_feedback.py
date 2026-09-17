"""feedback

Revision ID: 202609150001
Revises: 202609140001
Create Date: 2026-09-15 00:01:00
"""
from alembic import op
import sqlalchemy as sa

revision = "202609150001"
down_revision = "202609140001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "feedback",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(120), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("rating", sa.Integer(), nullable=True),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("feedback")
