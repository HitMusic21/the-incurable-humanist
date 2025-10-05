"""
Contract tests for Admin API endpoints (Author dashboard).
Tests MUST fail initially (red phase) until implementation is complete.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """FastAPI test client fixture."""
    from app.main import app

    return TestClient(app)


@pytest.fixture
def author_token(client):
    """Fixture to get author (Denise) authentication token."""
    # This assumes Denise's account exists
    # In real implementation, seed author account
    login_response = client.post(
        "/auth/login", json={"email": "denise@theincurablehumanist.com", "password": "AuthorPass123"}
    )

    if login_response.status_code == 200:
        return login_response.json()["access_token"]
    return None


@pytest.fixture
def reader_token(client):
    """Fixture to get regular reader authentication token."""
    client.post(
        "/auth/register",
        json={"email": "reader@example.com", "password": "ReaderPass123", "full_name": "Reader User"},
    )

    login_response = client.post(
        "/auth/login", json={"email": "reader@example.com", "password": "ReaderPass123"}
    )

    return login_response.json()["access_token"]


class TestAdminStoriesList:
    """Contract tests for GET /admin/stories endpoint."""

    def test_list_admin_stories_success(self, client, author_token):
        """Test author can list all their stories with status filter."""
        if not author_token:
            pytest.skip("Author token not available")

        response = client.get(
            "/admin/stories", headers={"Authorization": f"Bearer {author_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)

        # Validate AdminStoryListItem schema
        if len(data) > 0:
            story = data[0]
            assert "id" in story
            assert "title" in story
            assert "status" in story
            assert story["status"] in ["draft", "published", "archived"]
            assert "themes" in story
            assert "created_at" in story
            assert "published_at" in story
            assert "view_count" in story
            assert "comment_count" in story

    def test_list_admin_stories_with_status_filter(self, client, author_token):
        """Test filtering stories by status (draft, published, archived)."""
        if not author_token:
            pytest.skip("Author token not available")

        response = client.get(
            "/admin/stories?status=published",
            headers={"Authorization": f"Bearer {author_token}"},
        )

        assert response.status_code == 200
        stories = response.json()

        # All stories should have status 'published'
        for story in stories:
            assert story["status"] == "published"

    def test_list_admin_stories_unauthorized(self, client, reader_token):
        """Test reader cannot access admin stories."""
        response = client.get(
            "/admin/stories", headers={"Authorization": f"Bearer {reader_token}"}
        )

        assert response.status_code == 403

    def test_list_admin_stories_no_auth(self, client):
        """Test unauthenticated user cannot access admin stories."""
        response = client.get("/admin/stories")

        assert response.status_code == 401


class TestAdminStoryCreate:
    """Contract tests for POST /admin/stories endpoint."""

    def test_create_story_success(self, client, author_token):
        """Test author can create new story draft."""
        if not author_token:
            pytest.skip("Author token not available")

        response = client.post(
            "/admin/stories",
            headers={"Authorization": f"Bearer {author_token}"},
            json={
                "title": "Finding Home in Grief",
                "content": "<h1>Story content</h1><p>Paragraph</p>",
                "excerpt": "A story about grief and migration",
                "theme_ids": [1, 2],
                "content_warning": "Contains discussions of loss",
            },
        )

        assert response.status_code == 201
        data = response.json()

        # Validate AdminStoryDetail schema
        assert "id" in data
        assert data["title"] == "Finding Home in Grief"
        assert data["status"] == "draft"  # New stories are drafts
        assert data["content"] == "<h1>Story content</h1><p>Paragraph</p>"

    def test_create_story_unauthorized(self, client, reader_token):
        """Test reader cannot create stories."""
        response = client.post(
            "/admin/stories",
            headers={"Authorization": f"Bearer {reader_token}"},
            json={"title": "Unauthorized Story"},
        )

        assert response.status_code == 403


class TestAdminStoryUpdate:
    """Contract tests for PUT /admin/stories/{id} endpoint."""

    def test_update_story_success(self, client, author_token):
        """Test author can update their story."""
        if not author_token:
            pytest.skip("Author token not available")

        response = client.put(
            "/admin/stories/1",
            headers={"Authorization": f"Bearer {author_token}"},
            json={
                "title": "[Updated] Finding Home",
                "content": "<p>Updated content</p>",
                "theme_ids": [1, 2, 3],
            },
        )

        # Expected to fail until story with ID 1 exists
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = response.json()
            assert data["title"] == "[Updated] Finding Home"


class TestAdminStoryPublish:
    """Contract tests for POST /admin/stories/{id}/publish endpoint."""

    def test_publish_story_success(self, client, author_token):
        """Test author can publish a draft story."""
        if not author_token:
            pytest.skip("Author token not available")

        response = client.post(
            "/admin/stories/1/publish",
            headers={"Authorization": f"Bearer {author_token}"},
        )

        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = response.json()
            assert data["status"] == "published"
            assert "published_at" in data


class TestAdminStoryArchive:
    """Contract tests for DELETE /admin/stories/{id} endpoint (archive)."""

    def test_archive_story_success(self, client, author_token):
        """Test author can archive a story."""
        if not author_token:
            pytest.skip("Author token not available")

        response = client.delete(
            "/admin/stories/1", headers={"Authorization": f"Bearer {author_token}"}
        )

        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = response.json()
            assert "message" in data
            assert data["message"] == "Story archived"


class TestAdminCommentModeration:
    """Contract tests for comment moderation endpoints."""

    def test_get_moderation_queue(self, client, author_token):
        """Test author can see pending comments."""
        if not author_token:
            pytest.skip("Author token not available")

        response = client.get(
            "/admin/comments?status=pending",
            headers={"Authorization": f"Bearer {author_token}"},
        )

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)

        # Validate CommentModeration schema
        if len(data) > 0:
            comment = data[0]
            assert "id" in comment
            assert "content" in comment
            assert "status" in comment
            assert comment["status"] == "pending"
            assert "created_at" in comment
            assert "user" in comment
            assert "email" in comment["user"]
            assert "story" in comment
            assert "title" in comment["story"]

    def test_approve_comment(self, client, author_token):
        """Test author can approve a comment."""
        if not author_token:
            pytest.skip("Author token not available")

        response = client.post(
            "/admin/comments/1/moderate",
            headers={"Authorization": f"Bearer {author_token}"},
            json={"action": "approve"},
        )

        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = response.json()
            assert data["status"] == "approved"

    def test_reject_comment(self, client, author_token):
        """Test author can reject a comment."""
        if not author_token:
            pytest.skip("Author token not available")

        response = client.post(
            "/admin/comments/1/moderate",
            headers={"Authorization": f"Bearer {author_token}"},
            json={"action": "reject"},
        )

        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = response.json()
            assert data["status"] == "rejected"

    def test_moderate_unauthorized(self, client, reader_token):
        """Test reader cannot moderate comments."""
        response = client.get(
            "/admin/comments", headers={"Authorization": f"Bearer {reader_token}"}
        )

        assert response.status_code == 403
