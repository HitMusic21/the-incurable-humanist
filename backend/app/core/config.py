"""
Application configuration settings.
"""

import os

from pydantic_settings import BaseSettings, SettingsConfigDict

from .settings import normalize_database_url


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Attributes:
        DATABASE_URL: PostgreSQL connection string
        SECRET_KEY: JWT secret key
        ALGORITHM: JWT algorithm (HS256)
        ACCESS_TOKEN_EXPIRE_MINUTES: Token expiration time
        SENDGRID_API_KEY: SendGrid API key for emails
        AUTHOR_EMAIL: Denise's email (hardcoded author)
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/tih_db"

    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Email
    SENDGRID_API_KEY: str = ""

    # Application
    AUTHOR_EMAIL: str = "denise@theincurablehumanist.com"
    FRONTEND_URL: str = "http://localhost:5173"


# Initialize settings and normalize DATABASE_URL for Railway/asyncpg compatibility
_settings = Settings()
_settings.DATABASE_URL = normalize_database_url(os.getenv("DATABASE_URL", _settings.DATABASE_URL))

settings = _settings
