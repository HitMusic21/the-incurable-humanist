"""
Pydantic schemas for API request/response validation.
"""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


# ========== Auth Schemas ==========
class UserRegisterRequest(BaseModel):
    """User registration request schema."""

    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., max_length=255)


class UserLoginRequest(BaseModel):
    """User login request schema."""

    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """User response schema (safe - no password)."""

    id: int
    email: str
    full_name: str | None
    is_author: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Token response schema."""

    access_token: str
    token_type: str
    user: UserResponse


class PasswordResetRequest(BaseModel):
    """Password reset request schema."""

    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation schema."""

    new_password: str = Field(..., min_length=8)


# ========== Newsletter Schemas ==========
class NewsletterArticle(BaseModel):
    """Newsletter article schema from Substack RSS feed."""

    title: str
    link: str
    description: str
    published: str
    author: str | None = None


class NewsletterResponse(BaseModel):
    """Newsletter response schema containing list of articles."""

    articles: list[NewsletterArticle]
    total_count: int


# ========== Story Schemas ==========
class StoryCreate(BaseModel):
    """Author payload for POST /stories. `slug` optional — server generates from title."""

    title: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=1)  # Tiptap HTML
    slug: str | None = Field(default=None, max_length=255)
    excerpt: str | None = Field(default=None, max_length=500)
    meta_description: str | None = Field(default=None, max_length=320)
    cover_image_url: str | None = Field(default=None, max_length=500)
    canonical_url: str | None = Field(default=None, max_length=500)
    content_warning: str | None = Field(default=None, max_length=500)
    status: str = Field(default="draft")  # "draft" | "published" | "archived"


class StoryUpdate(BaseModel):
    """Partial update — every field optional."""

    title: str | None = Field(default=None, min_length=1, max_length=500)
    content: str | None = Field(default=None, min_length=1)
    slug: str | None = Field(default=None, max_length=255)
    excerpt: str | None = Field(default=None, max_length=500)
    meta_description: str | None = Field(default=None, max_length=320)
    cover_image_url: str | None = Field(default=None, max_length=500)
    canonical_url: str | None = Field(default=None, max_length=500)
    content_warning: str | None = Field(default=None, max_length=500)
    status: str | None = Field(default=None)


class StoryPublic(BaseModel):
    """Card/list projection — no full content."""

    id: int
    title: str
    slug: str
    excerpt: str | None
    meta_description: str | None
    cover_image_url: str | None
    canonical_url: str | None
    status: str
    published_at: datetime | None
    updated_at: datetime

    class Config:
        from_attributes = True


class StoryDetail(StoryPublic):
    """Full detail — includes body."""

    content: str
    content_warning: str | None
    view_count: int


class StoryListResponse(BaseModel):
    stories: list[StoryPublic]
    total_count: int
