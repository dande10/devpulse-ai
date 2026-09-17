"""feedback status

Revision ID: 202609160001
Revises: 202609150001
Create Date: 2026-09-16 00:01:00
"""
from alembic import op
import sqlalchemy as sa

revision = "202609160001"
down_revision = "202609150001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "feedback",
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
    )


def downgrade() -> None:
    op.drop_column("feedback", "status")
