"""
Story model for content authored by Denise.
"""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Column, types
from sqlmodel import Field, Relationship, SQLModel

# Import StoryTheme directly (needed at runtime for link_model)
from .theme import StoryTheme

if TYPE_CHECKING:
    from .bookmark import Bookmark
    from .comment import Comment
    from .reading_progress import ReadingProgress
    from .theme import Theme
    from .user import User


class StoryStatus(str, Enum):
    """Story publication status."""

    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class Story(SQLModel, table=True):
    """
    Story entity for author's published content.

    Attributes:
        id: Primary key
        title: Story title (max 500 chars)
        content: HTML content from Tiptap editor
        excerpt: Short summary for newsletters (max 500 chars)
        cover_image_url: Optional cover image
        status: Publication status (draft, published, archived)
        author_notes: Internal notes (searchable)
        content_warning: Optional content warning
        view_count: Number of views
        read_time_minutes: Calculated reading time
        author_id: Foreign key to User (must be author)
        created_at: Creation timestamp
        updated_at: Last update timestamp
        published_at: First publication timestamp
    """

    id: int | None = Field(default=None, primary_key=True)
    title: str = Field(max_length=500)
    content: str  # HTML from Tiptap editor
    excerpt: str | None = Field(default=None, max_length=500)
    cover_image_url: str | None = Field(default=None, max_length=500)
    status: StoryStatus = Field(default=StoryStatus.DRAFT)
    author_notes: str | None = Field(default=None)
    content_warning: str | None = Field(default=None, max_length=500)
    view_count: int = Field(default=0)
    read_time_minutes: int | None = Field(default=None)

    author_id: int = Field(foreign_key="user.id", index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    published_at: datetime | None = Field(default=None, index=True)

    # Full-text search vector (PostgreSQL TSVector)
    # Will be populated by trigger or service layer
    search_vector: str | None = Field(
        default=None, sa_column=Column(types.TEXT)
    )  # Simplified for now

    # Relationships
    author: "User" = Relationship(back_populates="stories")
    themes: list["Theme"] = Relationship(back_populates="stories", link_model=StoryTheme)
    comments: list["Comment"] = Relationship(back_populates="story")
    bookmarks: list["Bookmark"] = Relationship(back_populates="story")
    reading_progress: list["ReadingProgress"] = Relationship(back_populates="story")
