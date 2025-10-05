"""
Newsletter subscription model for reader preferences.
"""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Column
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .user import User


class NewsletterFrequency(str, Enum):
    """Newsletter delivery frequency options."""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class NewsletterSubscription(SQLModel, table=True):
    """
    Newsletter subscription entity for reader preferences.

    Attributes:
        id: Primary key
        user_id: Foreign key to User (unique - one subscription per user)
        frequency: Delivery frequency (daily, weekly, monthly)
        is_active: Subscription active status
        preferred_themes: JSON array of theme IDs for content filtering
        subscribed_at: Initial subscription timestamp
        unsubscribed_at: Unsubscribe timestamp (if inactive)
    """

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", unique=True, index=True)
    frequency: NewsletterFrequency = Field(default=NewsletterFrequency.WEEKLY)
    is_active: bool = Field(default=True, index=True)

    # Theme preferences (JSON array of theme IDs)
    preferred_themes: list[int] | None = Field(default=None, sa_column=Column(JSON))

    subscribed_at: datetime = Field(default_factory=datetime.utcnow)
    unsubscribed_at: datetime | None = Field(default=None)

    # Relationships
    user: "User" = Relationship(back_populates="subscription")
