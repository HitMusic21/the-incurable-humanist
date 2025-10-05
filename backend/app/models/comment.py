"""
Comment model for reader engagement on stories.
"""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .story import Story
    from .user import User


class CommentStatus(str, Enum):
    """Comment moderation status."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class Comment(SQLModel, table=True):
    """
    Comment entity for reader comments on stories.

    Attributes:
        id: Primary key
        content: Comment text (max 2000 chars)
        status: Moderation status (pending, approved, rejected)
        user_id: Foreign key to User (commenter)
        story_id: Foreign key to Story
        parent_id: Foreign key to Comment (for threaded replies)
        created_at: Comment creation timestamp
        moderated_at: Moderation decision timestamp
    """

    id: int | None = Field(default=None, primary_key=True)
    content: str = Field(max_length=2000)
    status: CommentStatus = Field(default=CommentStatus.PENDING, index=True)

    user_id: int = Field(foreign_key="user.id", index=True)
    story_id: int = Field(foreign_key="story.id", index=True)
    parent_id: int | None = Field(default=None, foreign_key="comment.id")

    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    moderated_at: datetime | None = Field(default=None)

    # Relationships
    user: "User" = Relationship(back_populates="comments")
    story: "Story" = Relationship(back_populates="comments")
    parent: Optional["Comment"] = Relationship(
        sa_relationship_kwargs={"remote_side": "Comment.id"}
    )
    replies: list["Comment"] = Relationship(
        back_populates="parent",
        sa_relationship_kwargs={"remote_side": "Comment.parent_id"}
    )
