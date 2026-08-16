"""lead_event audit table for SendGrid webhook events

Idempotent: skips creation if the table already exists (local dev may have
picked it up via SQLModel.metadata.create_all before Alembic ran).

Revision ID: 0004_lead_event
Revises: 0003_story_slug_notnull
Create Date: 2026-07-19
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision = "0004_lead_event"
down_revision = "0003_story_slug_notnull"
branch_labels = None
depends_on = None


def _table_exists(name: str) -> bool:
    return inspect(op.get_bind()).has_table(name)


def _existing_indexes(table: str) -> set[str]:
    return {idx["name"] for idx in inspect(op.get_bind()).get_indexes(table)}


def upgrade() -> None:
    if not _table_exists("lead_event"):
        op.create_table(
            "lead_event",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("lead_id", sa.Integer(), nullable=False),
            sa.Column("event_type", sa.String(length=32), nullable=False),
            sa.Column("sg_event_id", sa.String(length=128), nullable=False),
            sa.Column("payload_json", sa.Text(), nullable=True),
            sa.Column("occurred_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["lead_id"], ["lead_capture.id"]),
            sa.UniqueConstraint("sg_event_id", name="uq_lead_event_sg_event_id"),
        )

    indexes = _existing_indexes("lead_event")
    if "ix_lead_event_lead_id" not in indexes:
        op.create_index("ix_lead_event_lead_id", "lead_event", ["lead_id"])
    if "ix_lead_event_event_type" not in indexes:
        op.create_index("ix_lead_event_event_type", "lead_event", ["event_type"])
    if "ix_lead_event_sg_event_id" not in indexes:
        op.create_index("ix_lead_event_sg_event_id", "lead_event", ["sg_event_id"])
    if "ix_lead_event_occurred_at" not in indexes:
        op.create_index("ix_lead_event_occurred_at", "lead_event", ["occurred_at"])


def downgrade() -> None:
    if _table_exists("lead_event"):
        op.drop_table("lead_event")
