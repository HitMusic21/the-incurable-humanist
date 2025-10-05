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
