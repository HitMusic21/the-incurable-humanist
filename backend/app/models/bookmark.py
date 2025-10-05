"""
Bookmark model for reader's saved stories.
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .story import Story
    from .user import User


class Bookmark(SQLModel, table=True):
    """
    Bookmark entity for user's saved stories.

    Attributes:
        id: Primary key
        user_id: Foreign key to User
        story_id: Foreign key to Story
        created_at: Bookmark creation timestamp

    Constraints:
        Unique constraint on (user_id, story_id) - one bookmark per user per story
    """

    __table_args__ = (UniqueConstraint("user_id", "story_id", name="unique_user_story_bookmark"),)

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    story_id: int = Field(foreign_key="story.id", index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)

    # Relationships
    user: "User" = Relationship(back_populates="bookmarks")
    story: "Story" = Relationship(back_populates="bookmarks")
