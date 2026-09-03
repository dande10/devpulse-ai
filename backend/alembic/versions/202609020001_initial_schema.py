"""initial schema

Revision ID: 202609020001
Revises:
Create Date: 2026-09-02 00:01:00
"""
from alembic import op
import sqlalchemy as sa

revision = "202609020001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "technologies",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("slug", sa.String(120), nullable=False, unique=True),
        sa.Column("icon", sa.String(20), nullable=False),
        sa.Column("keywords", sa.JSON(), nullable=False),
        sa.Column("trusted_domains", sa.JSON(), nullable=False),
        sa.Column("official_domains", sa.JSON(), nullable=False),
        sa.Column("query_templates", sa.JSON(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("refresh_interval_hours", sa.Integer(), nullable=False, server_default="24"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_technologies_slug", "technologies", ["slug"])

    op.create_table(
        "sources",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("domain", sa.String(255), nullable=False, unique=True),
        sa.Column("source_type", sa.String(60), nullable=False),
        sa.Column("official", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("trust_score", sa.Integer(), nullable=False, server_default="80"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "developer_updates",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("canonical_url", sa.String(700), nullable=False, unique=True),
        sa.Column("source_id", sa.Integer(), sa.ForeignKey("sources.id"), nullable=False),
        sa.Column("original_excerpt", sa.Text(), nullable=True),
        sa.Column("extracted_content", sa.Text(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("why_it_matters", sa.Text(), nullable=True),
        sa.Column("recommended_action", sa.Text(), nullable=True),
        sa.Column("version", sa.String(80), nullable=True),
        sa.Column("category", sa.String(80), nullable=False),
        sa.Column("impact_level", sa.String(40), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("discovered_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("content_fingerprint", sa.String(128), nullable=False),
        sa.Column("raw_metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_updates_canonical_url", "developer_updates", ["canonical_url"])
    op.create_index("ix_updates_content_fingerprint", "developer_updates", ["content_fingerprint"])
    op.create_index("ix_updates_published_at", "developer_updates", ["published_at"])
    op.create_index("ix_updates_category", "developer_updates", ["category"])
    op.create_index("ix_updates_impact_level", "developer_updates", ["impact_level"])

    op.create_table(
        "update_technologies",
        sa.Column("update_id", sa.Integer(), sa.ForeignKey("developer_updates.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("technology_id", sa.Integer(), sa.ForeignKey("technologies.id", ondelete="CASCADE"), primary_key=True),
    )
    op.create_index("ix_update_technology_slug_join", "update_technologies", ["technology_id", "update_id"])

    op.create_table(
        "ingestion_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("technology_id", sa.Integer(), sa.ForeignKey("technologies.id"), nullable=True),
        sa.Column("tavily_endpoint", sa.String(80), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(40), nullable=False),
        sa.Column("results_found", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("results_saved", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("duplicates_skipped", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("ingestion_runs")
    op.drop_table("update_technologies")
    op.drop_table("developer_updates")
    op.drop_table("sources")
    op.drop_table("technologies")
