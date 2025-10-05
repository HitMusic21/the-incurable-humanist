"""
Database URL normalization utilities for Railway Postgres compatibility.
"""

import os
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse


def normalize_database_url(raw: str | None) -> str:
    """
    Normalize DATABASE_URL for asyncpg compatibility with Railway Postgres.

    Transformations:
    - Validates DATABASE_URL is set
    - Converts postgres:// to postgresql://
    - Adds +asyncpg driver if missing
    - Enforces sslmode=require for Railway Postgres (unless DB_SSLMODE overrides)

    Args:
        raw: Raw DATABASE_URL from environment

    Returns:
        Normalized PostgreSQL URL with asyncpg driver and SSL mode

    Raises:
        RuntimeError: If DATABASE_URL is not set

    Example:
        >>> normalize_database_url("postgres://user:pass@host:5432/db")
        "postgresql+asyncpg://user:pass@host:5432/db?sslmode=require"
    """
    if not raw:
        raise RuntimeError("DATABASE_URL is not set")

    # Convert postgres:// to postgresql://
    url = raw.replace("postgres://", "postgresql://")

    # Add asyncpg driver if missing
    if "+asyncpg" not in url:
        url = url.replace("postgresql://", "postgresql+asyncpg://")

    # Parse URL to add/modify query parameters
    parsed = urlparse(url)
    qs = dict(parse_qsl(parsed.query))

    # Set sslmode (default to 'require' for Railway, allow override via DB_SSLMODE)
    qs.setdefault("sslmode", os.getenv("DB_SSLMODE", "require"))

    # Rebuild query string
    new_query = urlencode(qs)

    # Reconstruct URL with updated query parameters
    normalized = urlunparse(parsed._replace(query=new_query))

    return normalized
