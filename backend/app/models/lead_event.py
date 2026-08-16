"""
Audit trail for SendGrid webhook events per lead. Purpose:

  - **Idempotency**: SendGrid retries webhook batches on non-2xx responses,
    and can also replay the same event on multiple batches. We unique-index
    `sg_event_id` so a re-delivery is a no-op INSERT.
  - **Diagnostics**: when a lead complains they never got the magnet, we
    can inspect delivered/opened/bounced/dropped rows without pulling
    SendGrid activity logs by hand.
"""

from datetime import datetime

from sqlmodel import Field, SQLModel


class LeadEvent(SQLModel, table=True):
    """One row per (lead, SendGrid event) pair — idempotent on sg_event_id."""

    __tablename__ = "lead_event"

    id: int | None = Field(default=None, primary_key=True)
    lead_id: int = Field(foreign_key="lead_capture.id", index=True)
    # SendGrid event types we care about: delivered, open, click, bounce,
    # spamreport, unsubscribe, dropped, deferred. Kept as freeform string to
    # tolerate future SendGrid additions without a migration.
    event_type: str = Field(max_length=32, index=True)
    # SendGrid's `sg_event_id` — globally unique per event, opaque string.
    sg_event_id: str = Field(max_length=128, unique=True, index=True)
    # Store the raw event JSON as a string for future replay/debug. Kept small
    # by only persisting the events we know about; skip firehose noise.
    payload_json: str | None = Field(default=None)
    occurred_at: datetime = Field(default_factory=datetime.utcnow, index=True)
