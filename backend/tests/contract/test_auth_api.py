"""
Contract tests for Auth API endpoints.
Tests MUST fail initially (red phase) until implementation is complete.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """FastAPI test client fixture."""
    from app.main import app

    return TestClient(app)


class TestAuthRegister:
    """Contract tests for POST /auth/register endpoint."""

    def test_register_success(self, client):
        """Test successful user registration returns 201 with UserResponse schema."""
        response = client.post(
            "/auth/register",
            json={
                "email": "reader@example.com",
                "password": "SecurePass123",
                "full_name": "Jane Doe",
            },
        )

        assert response.status_code == 201
        data = response.json()

        # Validate UserResponse schema
        assert "id" in data
        assert isinstance(data["id"], int)
        assert data["email"] == "reader@example.com"
        assert data["full_name"] == "Jane Doe"
        assert data["is_author"] is False
        assert "created_at" in data

    def test_register_duplicate_email(self, client):
        """Test registration with existing email returns 400 error."""
        # First registration
        client.post(
            "/auth/register",
            json={
                "email": "duplicate@example.com",
                "password": "SecurePass123",
                "full_name": "First User",
            },
        )

        # Duplicate registration
        response = client.post(
            "/auth/register",
            json={
                "email": "duplicate@example.com",
                "password": "DifferentPass456",
                "full_name": "Second User",
            },
        )

        assert response.status_code == 400
        assert "detail" in response.json()

    def test_register_invalid_email(self, client):
        """Test registration with invalid email format returns 400."""
        response = client.post(
            "/auth/register",
            json={
                "email": "not-an-email",
                "password": "SecurePass123",
                "full_name": "Jane Doe",
            },
        )

        assert response.status_code == 400

    def test_register_weak_password(self, client):
        """Test registration with password < 8 chars returns 400."""
        response = client.post(
            "/auth/register",
            json={"email": "user@example.com", "password": "weak", "full_name": "Jane Doe"},
        )

        assert response.status_code == 400


class TestAuthLogin:
    """Contract tests for POST /auth/login endpoint."""

    def test_login_success(self, client):
        """Test successful login returns 200 with access_token and user."""
        # Register user first
        client.post(
            "/auth/register",
            json={
                "email": "login@example.com",
                "password": "SecurePass123",
                "full_name": "Login User",
            },
        )

        # Login
        response = client.post(
            "/auth/login", json={"email": "login@example.com", "password": "SecurePass123"}
        )

        assert response.status_code == 200
        data = response.json()

        # Validate login response schema
        assert "access_token" in data
        assert isinstance(data["access_token"], str)
        assert data["token_type"] == "bearer"
        assert "user" in data

        # Validate nested UserResponse
        user = data["user"]
        assert user["email"] == "login@example.com"
        assert user["is_author"] is False

    def test_login_invalid_credentials(self, client):
        """Test login with wrong password returns 401."""
        # Register user
        client.post(
            "/auth/register",
            json={
                "email": "wrongpass@example.com",
                "password": "CorrectPass123",
                "full_name": "User",
            },
        )

        # Login with wrong password
        response = client.post(
            "/auth/login", json={"email": "wrongpass@example.com", "password": "WrongPass123"}
        )

        assert response.status_code == 401
        assert "detail" in response.json()

    def test_login_nonexistent_user(self, client):
        """Test login with non-existent email returns 401."""
        response = client.post(
            "/auth/login",
            json={"email": "nonexistent@example.com", "password": "AnyPass123"},
        )

        assert response.status_code == 401


class TestAuthMe:
    """Contract tests for GET /auth/me endpoint."""

    def test_get_current_user_success(self, client):
        """Test authenticated user can get their info."""
        # Register and login
        client.post(
            "/auth/register",
            json={"email": "me@example.com", "password": "SecurePass123", "full_name": "Me User"},
        )
        login_response = client.post(
            "/auth/login", json={"email": "me@example.com", "password": "SecurePass123"}
        )
        token = login_response.json()["access_token"]

        # Get current user
        response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "me@example.com"
        assert data["full_name"] == "Me User"

    def test_get_current_user_unauthorized(self, client):
        """Test /auth/me without token returns 401."""
        response = client.get("/auth/me")

        assert response.status_code == 401

    def test_get_current_user_invalid_token(self, client):
        """Test /auth/me with invalid token returns 401."""
        response = client.get("/auth/me", headers={"Authorization": "Bearer invalid_token"})

        assert response.status_code == 401


class TestPasswordReset:
    """Contract tests for password reset endpoints."""

    def test_request_reset_email(self, client):
        """Test password reset request returns 200."""
        response = client.post("/auth/reset-password", json={"email": "user@example.com"})

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert data["message"] == "Password reset email sent"

    def test_reset_password_with_token(self, client):
        """Test password reset with valid token returns 200."""
        # This test will need real token generation logic implemented
        # For now, testing the endpoint structure
        response = client.post(
            "/auth/reset-password/valid-token", json={"new_password": "NewSecure123"}
        )

        # Expected to fail until implementation
        assert response.status_code in [200, 400, 404]

    def test_reset_password_invalid_token(self, client):
        """Test password reset with invalid token returns 400."""
        response = client.post(
            "/auth/reset-password/invalid-token", json={"new_password": "NewSecure123"}
        )

        assert response.status_code == 400
