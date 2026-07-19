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

    # Email — SendGrid transactional (double opt-in, magnet, welcome sequence)
    SENDGRID_API_KEY: str = ""
    SENDGRID_FROM_EMAIL: str = "hello@theincurablehumanist.com"
    SENDGRID_FROM_NAME: str = "Denise Rodriguez Dao"
    SENDGRID_WEBHOOK_KEY: str = ""  # verifies /leads/sendgrid/webhook signatures (Tier 4)
    # Dynamic template IDs — configured in SendGrid UI, referenced by env
    SENDGRID_TPL_CONFIRM: str = ""
    SENDGRID_TPL_MAGNET: str = ""
    SENDGRID_TPL_SEQ_1: str = ""
    SENDGRID_TPL_SEQ_2: str = ""
    SENDGRID_TPL_SEQ_3: str = ""
    SENDGRID_TPL_SEQ_4: str = ""
    SENDGRID_TPL_SEQ_5: str = ""

    # Lead magnet PDF (served from frontend/public/reader/)
    MAGNET_PDF_URL: str = "/reader/starter-reader.pdf"

    # Scheduler protection — required header for POST /leads/sequence/tick (Tier 3)
    SCHEDULER_TOKEN: str = ""

    # PostHog server-side capture (Tier 4 SendGrid webhook mirror)
    POSTHOG_API_KEY: str = ""
    POSTHOG_HOST: str = "https://us.i.posthog.com"
    # SendGrid Event Webhook signing key — the ECDSA public key from the
    # SendGrid portal. Set to enable signature verification on the webhook.
    # If unset, webhook is 503 (fail-closed) in the same spirit as
    # SCHEDULER_TOKEN — never accept unauthenticated event ingestion in prod.
    SENDGRID_WEBHOOK_PUBLIC_KEY: str = ""

    # Application
    AUTHOR_EMAIL: str = "denise@theincurablehumanist.com"
    FRONTEND_URL: str = "http://localhost:5173"


# Initialize settings and normalize DATABASE_URL for Railway/asyncpg compatibility
_settings = Settings()
_settings.DATABASE_URL = normalize_database_url(os.getenv("DATABASE_URL", _settings.DATABASE_URL))

settings = _settings
