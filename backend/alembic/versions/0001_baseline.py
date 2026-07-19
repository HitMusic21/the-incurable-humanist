"""baseline (no-op) — assume tables already exist via init_db() / create_all

This migration is a no-op. It exists so `alembic stamp head` can mark a fresh
database (created by `SQLModel.metadata.create_all` at app startup) as being
"at the baseline," letting subsequent migrations apply cleanly.

Rationale: the project ran `create_all` at boot from day one, so prod schemas
were never controlled by migrations. Rather than reverse-engineer a baseline
from live schema (drift risk), we treat "whatever create_all produced" as the
starting point. All schema changes from this point forward are versioned.

Revision ID: 0001_baseline
Revises:
Create Date: 2026-07-19
"""

from alembic import op  # noqa: F401
import sqlalchemy as sa  # noqa: F401


revision = "0001_baseline"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Intentional no-op — baseline is whatever SQLModel.metadata.create_all built.
    pass


def downgrade() -> None:
    pass
