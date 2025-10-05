"""
Authentication service for user registration and login.
"""

from datetime import timedelta
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
from app.core.database import get_session
from app.core.security import create_access_token, decode_access_token, hash_password, verify_password
from app.models import User

security = HTTPBearer()


async def register_user(
    email: str,
    password: str,
    full_name: str,
    session: AsyncSession,
) -> User:
    """
    Register a new user.

    Args:
        email: User email (unique)
        password: Plain text password (min 8 chars)
        full_name: User's full name
        session: Database session

    Returns:
        Created User instance

    Raises:
        HTTPException: If email already exists or validation fails
    """
    # Check if email already exists
    result = await session.execute(select(User).where(User.email == email.lower()))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Validate password length
    if len(password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters",
        )

    # Create new user
    hashed_password = hash_password(password)

    # Check if this is the author (Denise)
    is_author = email.lower() == settings.AUTHOR_EMAIL.lower()

    user = User(
        email=email.lower(),
        hashed_password=hashed_password,
        full_name=full_name,
        is_author=is_author,
    )

    session.add(user)
    await session.commit()
    await session.refresh(user)

    return user


async def authenticate_user(
    email: str,
    password: str,
    session: AsyncSession,
) -> User | None:
    """
    Authenticate user with email and password.

    Args:
        email: User email
        password: Plain text password
        session: Database session

    Returns:
        User instance if authenticated, None otherwise
    """
    result = await session.execute(select(User).where(User.email == email.lower()))
    user = result.scalar_one_or_none()

    if not user:
        return None

    if not verify_password(password, user.hashed_password):
        return None

    return user


def create_user_token(user: User) -> dict[str, Any]:
    """
    Create access token for user.

    Args:
        user: User instance

    Returns:
        Dict with access_token and token_type
    """
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "is_author": user.is_author}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_session),
) -> User:
    """
    Get current authenticated user from JWT token.

    Args:
        credentials: HTTP Bearer credentials
        session: Database session

    Returns:
        Current User instance

    Raises:
        HTTPException: If token is invalid or user not found
    """
    token = credentials.credentials
    payload = decode_access_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )

    user_id = payload.get("sub")

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )

    result = await session.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user


async def get_current_author(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Verify current user is the author (Denise).

    Args:
        current_user: Current authenticated user

    Returns:
        Author User instance

    Raises:
        HTTPException: If user is not the author
    """
    if not current_user.is_author:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized. Author access required.",
        )

    return current_user
