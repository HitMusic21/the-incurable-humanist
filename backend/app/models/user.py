"""
User model representing both readers and the author (Denise).
"""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .bookmark import Bookmark
    from .comment import Comment
    from .newsletter import NewsletterSubscription
    from .reading_progress import ReadingProgress
    from .story import Story


class User(SQLModel, table=True):
    """
    User entity for both readers and author.

    Attributes:
        id: Primary key
        email: Unique email address (case-insensitive lookups)
        hashed_password: Bcrypt hashed password
        full_name: User's full name
        is_author: True only for Denise Rodriguez Dao
        is_active: Account active status
        created_at: Account creation timestamp
    """

    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True, max_length=255)
    hashed_password: str
    full_name: str | None = Field(default=None, max_length=255)
    is_author: bool = Field(default=False, index=True)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    stories: list["Story"] = Relationship(back_populates="author")
    comments: list["Comment"] = Relationship(back_populates="user")
    bookmarks: list["Bookmark"] = Relationship(back_populates="user")
    subscription: Optional["NewsletterSubscription"] = Relationship(back_populates="user")
    reading_progress: list["ReadingProgress"] = Relationship(back_populates="user")
