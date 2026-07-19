"""story.slug NOT NULL after backfill

Runs after `backend/scripts/backfill_story_slugs.py` (or a manual UPDATE for
any legacy rows). Safe to run against a fresh DB — the WHERE-NOT-NULL filter
is a no-op when the table is empty.

Revision ID: 0003_story_slug_notnull
Revises: 0002_story_seo_fields
Create Date: 2026-07-19
"""

import sqlalchemy as sa
from alembic import op


revision = "0003_story_slug_notnull"
down_revision = "0002_story_seo_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Sanity check: fail loudly if any row is missing a slug.
    bind = op.get_bind()
    missing = bind.execute(sa.text("SELECT COUNT(*) FROM story WHERE slug IS NULL")).scalar()
    if missing and missing > 0:
        raise RuntimeError(
            f"{missing} story rows have NULL slug. Run "
            "`python backend/scripts/backfill_story_slugs.py` before upgrading."
        )
    op.alter_column("story", "slug", existing_type=sa.String(length=255), nullable=False)


def downgrade() -> None:
    op.alter_column("story", "slug", existing_type=sa.String(length=255), nullable=True)
