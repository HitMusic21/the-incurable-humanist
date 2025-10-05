"""
Authentication API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.services.auth import (
    authenticate_user,
    create_user_token,
    get_current_user,
    register_user,
)

from .schemas import (
    PasswordResetConfirm,
    PasswordResetRequest,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: UserRegisterRequest,
    session: AsyncSession = Depends(get_session),
):
    """
    Register a new user account.

    - **email**: Valid email address (unique)
    - **password**: Min 8 characters
    - **full_name**: User's full name
    """
    user = await register_user(
        email=request.email,
        password=request.password,
        full_name=request.full_name,
        session=session,
    )

    return user


@router.post("/login", response_model=TokenResponse)
async def login(
    request: UserLoginRequest,
    session: AsyncSession = Depends(get_session),
):
    """
    Login with email and password.

    Returns JWT access token and user info.
    """
    user = await authenticate_user(
        email=request.email,
        password=request.password,
        session=session,
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token_data = create_user_token(user)

    return {
        **token_data,
        "user": UserResponse.model_validate(user),
    }


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user = Depends(get_current_user),
):
    """
    Get current authenticated user info.

    Requires valid JWT token in Authorization header.
    """
    return current_user


@router.post("/reset-password")
async def request_password_reset(
    request: PasswordResetRequest,
    session: AsyncSession = Depends(get_session),
):
    """
    Request password reset email.

    Always returns success to prevent email enumeration.
    """
    # TODO: Implement password reset email logic with SendGrid
    # For now, always return success message
    return {"message": "Password reset email sent"}


@router.post("/reset-password/{token}")
async def reset_password(
    token: str,
    request: PasswordResetConfirm,
    session: AsyncSession = Depends(get_session),
):
    """
    Reset password with token from email.

    - **token**: Password reset token from email
    - **new_password**: New password (min 8 characters)
    """
    # TODO: Implement password reset token validation and password update
    # For now, return error
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid or expired token",
    )
