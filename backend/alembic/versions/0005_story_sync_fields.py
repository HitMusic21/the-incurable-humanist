"""story sync fields: source_url, content_hash, content_source

Adds the columns the Substack sync needs, plus a unique index on source_url
(the sync's idempotency key).

Idempotent against a `create_all` schema — app startup runs
SQLModel.metadata.create_all, so on a local dev DB these columns may already
exist. We inspect first and no-op in that case, same as 0002/0004.

Two data statements run in order, and the SECOND IS NOT OPTIONAL:
  1. move provenance from canonical_url -> source_url for any rows left by the
     old scripts/import_substack.py;
  2. THEN clear canonical_url on those rows. EssayDetail.tsx prefers
     canonical_url whenever it is non-empty, so a row with both fields set
     would still emit an off-domain <link rel="canonical"> pointing at
     Substack — silently de-indexing the on-site essay.

Revision ID: 0005_story_sync_fields
Revises: 0004_lead_event
Create Date: 2026-08-16
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision = "0005_story_sync_fields"
down_revision = "0004_lead_event"
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
    if "source_url" not in cols:
        op.add_column("story", sa.Column("source_url", sa.String(length=500), nullable=True))
    if "content_hash" not in cols:
        op.add_column("story", sa.Column("content_hash", sa.String(length=64), nullable=True))
    if "content_source" not in cols:
        op.add_column("story", sa.Column("content_source", sa.String(length=8), nullable=True))

    if "ix_story_source_url" not in _existing_indexes("story"):
        op.create_index("ix_story_source_url", "story", ["source_url"], unique=True)

    # 1. Carry provenance across from the legacy importer.
    op.execute(
        """
        UPDATE story SET source_url = canonical_url
         WHERE canonical_url IS NOT NULL AND source_url IS NULL
        """
    )
    # 2. Clear canonical so the on-site page is canonical. See module docstring.
    op.execute(
        """
        UPDATE story SET canonical_url = NULL
         WHERE source_url IS NOT NULL AND canonical_url = source_url
        """
    )


def downgrade() -> None:
    # Restore canonical_url from source_url so the pre-0005 SEO behaviour returns.
    op.execute(
        """
        UPDATE story SET canonical_url = source_url
         WHERE source_url IS NOT NULL AND canonical_url IS NULL
        """
    )

    if "ix_story_source_url" in _existing_indexes("story"):
        op.drop_index("ix_story_source_url", table_name="story")

    cols = _existing_columns("story")
    for col in ("content_source", "content_hash", "source_url"):
        if col in cols:
            op.drop_column("story", col)
