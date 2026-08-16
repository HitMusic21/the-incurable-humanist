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
    - Enforces ssl=require for Railway Postgres (asyncpg uses 'ssl', not 'sslmode')
    - Converts sslmode=require to ssl=require for asyncpg compatibility

    Args:
        raw: Raw DATABASE_URL from environment

    Returns:
        Normalized PostgreSQL URL with asyncpg driver and SSL configuration

    Raises:
        RuntimeError: If DATABASE_URL is not set

    Example:
        >>> normalize_database_url("postgres://user:pass@host:5432/db")
        "postgresql+asyncpg://user:pass@host:5432/db?ssl=require"
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

    # Convert sslmode to ssl for asyncpg compatibility
    # asyncpg uses 'ssl' parameter, not 'sslmode'
    if "sslmode" in qs:
        ssl_value = qs.pop("sslmode")
        # Map common sslmode values to asyncpg ssl parameter
        if ssl_value in ("require", "verify-ca", "verify-full"):
            qs["ssl"] = "require"
        elif ssl_value == "prefer":
            qs["ssl"] = "prefer"
        # 'disable' or 'allow' - don't set ssl parameter

    # Set ssl parameter (default to 'require' for Railway, allow override via DB_SSL)
    # Only set if not already present and sslmode wasn't disable/allow
    if "ssl" not in qs:
        ssl_mode = os.getenv("DB_SSL", "require")
        if ssl_mode != "disable":
            qs["ssl"] = ssl_mode

    # Rebuild query string
    new_query = urlencode(qs)

    # Reconstruct URL with updated query parameters
    normalized = urlunparse(parsed._replace(query=new_query))

    return normalized
