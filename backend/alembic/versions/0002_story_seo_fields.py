"""story SEO fields: slug, canonical_url, meta_description

Adds nullable columns + unique index on slug. Migration 0003 backfills and
enforces NOT NULL. Idempotent against a `create_all` schema — the columns
may already exist in local dev (SQLModel picked them up); we no-op in that case.

Revision ID: 0002_story_seo_fields
Revises: 0001_baseline
Create Date: 2026-07-19
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect


revision = "0002_story_seo_fields"
down_revision = "0001_baseline"
branch_labels = None
depends_on = None


def _existing_columns(table: str) -> set[str]:
    bind = op.get_bind()
    inspector = inspect(bind)
    return {col["name"] for col in inspector.get_columns(table)}


def _existing_indexes(table: str) -> set[str]:
    bind = op.get_bind()
    inspector = inspect(bind)
    return {idx["name"] for idx in inspector.get_indexes(table)}


def upgrade() -> None:
    cols = _existing_columns("story")
    if "slug" not in cols:
        op.add_column("story", sa.Column("slug", sa.String(length=255), nullable=True))
    if "canonical_url" not in cols:
        op.add_column("story", sa.Column("canonical_url", sa.String(length=500), nullable=True))
    if "meta_description" not in cols:
        op.add_column("story", sa.Column("meta_description", sa.String(length=320), nullable=True))

    indexes = _existing_indexes("story")
    if "ix_story_slug" not in indexes:
        op.create_index("ix_story_slug", "story", ["slug"], unique=True)


def downgrade() -> None:
    indexes = _existing_indexes("story")
    if "ix_story_slug" in indexes:
        op.drop_index("ix_story_slug", table_name="story")
    cols = _existing_columns("story")
    for col in ("meta_description", "canonical_url", "slug"):
        if col in cols:
            op.drop_column("story", col)
