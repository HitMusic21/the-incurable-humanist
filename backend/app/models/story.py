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
    # Nullable at the model level so imports without a title-derived slug can
    # be introduced by migration + backfill; NOT NULL enforced in migration 0003.
    slug: str | None = Field(default=None, max_length=255, unique=True, index=True)
    # If set, points to the canonical version off-site (e.g. Substack URL) and
    # is emitted as <link rel="canonical"> on the essay page. Clear when the
    # on-site page becomes canonical.
    canonical_url: str | None = Field(default=None, max_length=500)
    # Provenance: the Substack permalink this row was synced from. Distinct from
    # canonical_url — we are canonical; this only drives the "first published on
    # Substack" credit link and is the idempotency key for the sync job.
    source_url: str | None = Field(default=None, max_length=500, unique=True, index=True)
    # sha256 of normalized TEXT (not markup). Substack's RSS and its JSON API
    # render identical prose with different image markup (<picture>+srcset vs a
    # bare <img>), so hashing markup would mark every row changed on every sync.
    content_hash: str | None = Field(default=None, max_length=64)
    # 'api' (rich <picture>/srcset) or 'rss' (plain <img>). Guards against an RSS
    # sync overwriting richer image markup on a row backfilled from the API.
    content_source: str | None = Field(default=None, max_length=8)
    # Overrides <meta name="description"> — falls back to excerpt when empty.
    meta_description: str | None = Field(default=None, max_length=320)
    content: str  # HTML from Tiptap editor
    excerpt: str | None = Field(default=None, max_length=500)
    cover_image_url: str | None = Field(default=None, max_length=500)
    status: StoryStatus = Field(default=StoryStatus.DRAFT, index=True)
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
