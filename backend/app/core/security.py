"""
Security utilities for authentication and authorization.
"""

import logging
from datetime import datetime, timedelta
from typing import Any

from fastapi import HTTPException
from jose import JWTError, jwt
from passlib.context import CryptContext

from .config import settings

logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# The public default this project shipped with. Anyone could forge tokens with it.
_INSECURE_SECRET_KEYS = {"", "your-secret-key-change-in-production"}


def _require_secret_key() -> str:
    """Fail closed rather than sign/verify JWTs with a guessable key."""
    if settings.SECRET_KEY in _INSECURE_SECRET_KEYS:
        logger.error("Auth request rejected: SECRET_KEY is not configured.")
        raise HTTPException(status_code=503, detail="Auth not configured.")
    return settings.SECRET_KEY


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: Plain text password

    Returns:
        Hashed password string
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password to compare against

    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """
    Create a JWT access token.

    Args:
        data: Payload data to encode in token
        expires_delta: Token expiration time (defaults to settings value)

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, _require_secret_key(), algorithm=settings.ALGORITHM)

    return encoded_jwt


def decode_access_token(token: str) -> dict[str, Any] | None:
    """
    Decode and validate a JWT access token.

    Args:
        token: JWT token string

    Returns:
        Decoded token payload dict, or None if invalid
    """
    try:
        payload = jwt.decode(token, _require_secret_key(), algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None
