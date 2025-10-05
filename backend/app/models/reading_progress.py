"""
Reading progress model to track reader position in stories.
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .story import Story
    from .user import User


class ReadingProgress(SQLModel, table=True):
    """
    Reading progress entity for tracking story completion.

    Attributes:
        id: Primary key
        user_id: Foreign key to User
        story_id: Foreign key to Story
        progress_percent: Reading progress (0-100)
        last_read_at: Last reading timestamp

    Constraints:
        Unique constraint on (user_id, story_id) - one progress per user per story
    """

    __table_args__ = (
        UniqueConstraint("user_id", "story_id", name="unique_user_story_progress"),
    )

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    story_id: int = Field(foreign_key="story.id", index=True)
    progress_percent: int = Field(default=0, ge=0, le=100)  # 0-100%
    last_read_at: datetime = Field(default_factory=datetime.utcnow, index=True)

    # Relationships
    user: "User" = Relationship(back_populates="reading_progress")
    story: "Story" = Relationship(back_populates="reading_progress")
