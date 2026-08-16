"""
Anonymous newsletter lead capture — separate from NewsletterSubscription (which is user-scoped).

Handles the double opt-in flow for the lead-magnet PDF and drives the 5-email
welcome sequence. See docs/plan for the funnel design.
"""

from datetime import datetime

from sqlmodel import Field, SQLModel


class LeadCapture(SQLModel, table=True):
    """Anonymous email capture from SubscribeCTA / ExitIntentModal."""

    __tablename__ = "lead_capture"

    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(max_length=254, index=True, unique=True)

    # Funnel attribution
    source: str = Field(max_length=64)  # e.g. "home-hero", "exit-intent", "archive-primary"
    utm_source: str | None = Field(default=None, max_length=64)
    utm_medium: str | None = Field(default=None, max_length=64)
    utm_campaign: str | None = Field(default=None, max_length=128)
    utm_content: str | None = Field(default=None, max_length=128)
    utm_term: str | None = Field(default=None, max_length=128)
    referrer_url: str | None = Field(default=None, max_length=500)

    # Double opt-in
    magnet_requested: bool = Field(default=True)
    confirmation_token: str = Field(max_length=64, unique=True, index=True)
    confirmed_at: datetime | None = Field(default=None)
    unsubscribed_at: datetime | None = Field(default=None)

    # Welcome sequence state (Tier 3)
    sequence_step: int = Field(default=0)  # 0..5, last welcome email delivered
    next_send_at: datetime | None = Field(default=None, index=True)

    created_at: datetime = Field(default_factory=datetime.utcnow)
