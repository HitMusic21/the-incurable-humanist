"""
Theme model and StoryTheme junction table.
"""

from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .story import Story


# Define junction table FIRST (before references)
class StoryTheme(SQLModel, table=True):
    """
    Junction table for many-to-many Story-Theme relationship.

    Attributes:
        story_id: Foreign key to Story (composite primary key)
        theme_id: Foreign key to Theme (composite primary key)
    """

    story_id: int = Field(foreign_key="story.id", primary_key=True)
    theme_id: int = Field(foreign_key="theme.id", primary_key=True)


class Theme(SQLModel, table=True):
    """
    Theme entity for story categorization.

    Attributes:
        id: Primary key
        name: Theme name (unique, lowercase)
        slug: URL-friendly identifier (unique)
        description: Optional theme description
    """

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(unique=True, max_length=50, index=True)
    slug: str = Field(unique=True, max_length=50, index=True)
    description: str | None = Field(default=None, max_length=500)

    # Relationships
    stories: list["Story"] = Relationship(back_populates="themes", link_model=StoryTheme)
