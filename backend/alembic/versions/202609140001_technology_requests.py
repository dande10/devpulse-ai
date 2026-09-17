"""technology requests

Revision ID: 202609140001
Revises: 202609020001
Create Date: 2026-09-14 00:01:00
"""
from alembic import op
import sqlalchemy as sa

revision = "202609140001"
down_revision = "202609020001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "technology_requests",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("normalized_name", sa.String(120), nullable=False, unique=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("request_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_technology_requests_normalized_name", "technology_requests", ["normalized_name"])
    op.create_index("ix_technology_requests_status", "technology_requests", ["status"])


def downgrade() -> None:
    op.drop_table("technology_requests")
