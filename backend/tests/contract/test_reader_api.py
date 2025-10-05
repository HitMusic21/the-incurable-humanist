"""
Contract tests for Reader API endpoints (engagement features).
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
def reader_token(client):
    """Fixture to get authenticated reader token."""
    client.post(
        "/auth/register",
        json={
            "email": "engagement@example.com",
            "password": "ReaderPass123",
            "full_name": "Engaged Reader",
        },
    )

    login_response = client.post(
        "/auth/login", json={"email": "engagement@example.com", "password": "ReaderPass123"}
    )

    return login_response.json()["access_token"]


class TestComments:
    """Contract tests for comment endpoints."""

    def test_get_story_comments(self, client):
        """Test getting approved comments for a story."""
        response = client.get("/stories/1/comments")

        # Expected to fail until story exists
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)

            # Validate Comment schema
            if len(data) > 0:
                comment = data[0]
                assert "id" in comment
                assert "content" in comment
                assert "status" in comment
                assert comment["status"] == "approved"  # Only approved shown publicly
                assert "created_at" in comment
                assert "user" in comment
                assert "full_name" in comment["user"]
                assert "parent_id" in comment  # For threading
                assert "replies" in comment  # Nested replies

    def test_submit_comment_authenticated(self, client, reader_token):
        """Test authenticated reader can submit comment."""
        response = client.post(
            "/stories/1/comments",
            headers={"Authorization": f"Bearer {reader_token}"},
            json={"content": "Beautiful story about grief and healing"},
        )

        # Expected to fail until story exists
        assert response.status_code in [201, 404, 401]

        if response.status_code == 201:
            data = response.json()
            assert data["content"] == "Beautiful story about grief and healing"
            assert data["status"] == "pending"  # Awaiting moderation

    def test_submit_threaded_reply(self, client, reader_token):
        """Test submitting a reply to existing comment."""
        response = client.post(
            "/stories/1/comments",
            headers={"Authorization": f"Bearer {reader_token}"},
            json={"content": "I agree with your perspective", "parent_id": 1},
        )

        assert response.status_code in [201, 404, 401]

        if response.status_code == 201:
            data = response.json()
            assert data["parent_id"] == 1

    def test_submit_comment_unauthenticated(self, client):
        """Test unauthenticated user cannot submit comment."""
        response = client.post(
            "/stories/1/comments", json={"content": "This should be rejected"}
        )

        assert response.status_code == 401

    def test_comment_max_length_validation(self, client, reader_token):
        """Test comment content max length is 2000 chars."""
        long_content = "a" * 2001

        response = client.post(
            "/stories/1/comments",
            headers={"Authorization": f"Bearer {reader_token}"},
            json={"content": long_content},
        )

        assert response.status_code in [400, 422]


class TestBookmarks:
    """Contract tests for bookmark endpoints."""

    def test_get_user_bookmarks(self, client, reader_token):
        """Test authenticated user can get their bookmarks."""
        response = client.get("/bookmarks", headers={"Authorization": f"Bearer {reader_token}"})

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)

        # Validate BookmarkedStory schema
        if len(data) > 0:
            bookmark = data[0]
            assert "id" in bookmark
            assert "story_id" in bookmark
            assert "created_at" in bookmark
            assert "story" in bookmark

            # Nested story details
            story = bookmark["story"]
            assert "id" in story
            assert "title" in story
            assert "excerpt" in story
            assert "themes" in story

    def test_bookmark_story(self, client, reader_token):
        """Test authenticated user can bookmark a story."""
        response = client.post(
            "/bookmarks",
            headers={"Authorization": f"Bearer {reader_token}"},
            json={"story_id": 1},
        )

        # Expected to fail until story exists
        assert response.status_code in [201, 404, 400]

        if response.status_code == 201:
            data = response.json()
            assert data["story_id"] == 1

    def test_bookmark_duplicate(self, client, reader_token):
        """Test bookmarking same story twice returns 400."""
        # First bookmark
        client.post(
            "/bookmarks",
            headers={"Authorization": f"Bearer {reader_token}"},
            json={"story_id": 1},
        )

        # Duplicate bookmark
        response = client.post(
            "/bookmarks",
            headers={"Authorization": f"Bearer {reader_token}"},
            json={"story_id": 1},
        )

        assert response.status_code == 400

    def test_remove_bookmark(self, client, reader_token):
        """Test removing a bookmark."""
        # First bookmark the story
        client.post(
            "/bookmarks",
            headers={"Authorization": f"Bearer {reader_token}"},
            json={"story_id": 1},
        )

        # Remove bookmark
        response = client.delete(
            "/bookmarks/1", headers={"Authorization": f"Bearer {reader_token}"}
        )

        assert response.status_code in [200, 404]

    def test_bookmarks_require_auth(self, client):
        """Test bookmarks require authentication."""
        response = client.get("/bookmarks")

        assert response.status_code == 401


class TestReadingProgress:
    """Contract tests for reading progress endpoints."""

    def test_update_reading_progress(self, client, reader_token):
        """Test updating reading progress for a story."""
        response = client.post(
            "/reading-progress",
            headers={"Authorization": f"Bearer {reader_token}"},
            json={"story_id": 1, "progress_percent": 50},
        )

        # Expected to fail until story exists
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = response.json()
            assert data["story_id"] == 1
            assert data["progress_percent"] == 50
            assert "last_read_at" in data

    def test_progress_validation(self, client, reader_token):
        """Test progress_percent must be 0-100."""
        # Test below minimum
        response = client.post(
            "/reading-progress",
            headers={"Authorization": f"Bearer {reader_token}"},
            json={"story_id": 1, "progress_percent": -10},
        )

        assert response.status_code in [400, 422]

        # Test above maximum
        response = client.post(
            "/reading-progress",
            headers={"Authorization": f"Bearer {reader_token}"},
            json={"story_id": 1, "progress_percent": 150},
        )

        assert response.status_code in [400, 422]

    def test_get_all_reading_progress(self, client, reader_token):
        """Test getting reading progress for all stories."""
        response = client.get(
            "/reading-progress", headers={"Authorization": f"Bearer {reader_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)

        # Validate ReadingProgress schema
        if len(data) > 0:
            progress = data[0]
            assert "story_id" in progress
            assert "progress_percent" in progress
            assert "last_read_at" in progress

    def test_progress_requires_auth(self, client):
        """Test reading progress requires authentication."""
        response = client.post(
            "/reading-progress", json={"story_id": 1, "progress_percent": 50}
        )

        assert response.status_code == 401


class TestNewsletterSubscription:
    """Contract tests for newsletter subscription endpoints."""

    def test_subscribe_to_newsletter(self, client, reader_token):
        """Test authenticated user can subscribe to newsletter."""
        response = client.post(
            "/newsletter/subscribe",
            headers={"Authorization": f"Bearer {reader_token}"},
            json={"frequency": "weekly", "preferred_themes": [1, 2]},
        )

        assert response.status_code == 200
        data = response.json()

        # Validate Subscription schema
        assert "id" in data
        assert data["frequency"] == "weekly"
        assert data["preferred_themes"] == [1, 2]
        assert data["is_active"] is True
        assert "subscribed_at" in data

    def test_subscribe_frequency_validation(self, client, reader_token):
        """Test frequency must be daily, weekly, or monthly."""
        response = client.post(
            "/newsletter/subscribe",
            headers={"Authorization": f"Bearer {reader_token}"},
            json={"frequency": "invalid_frequency"},
        )

        assert response.status_code in [400, 422]

    def test_subscribe_valid_frequencies(self, client, reader_token):
        """Test all valid frequency options."""
        for frequency in ["daily", "weekly", "monthly"]:
            response = client.post(
                "/newsletter/subscribe",
                headers={"Authorization": f"Bearer {reader_token}"},
                json={"frequency": frequency},
            )

            assert response.status_code == 200
            assert response.json()["frequency"] == frequency

    def test_unsubscribe_from_newsletter(self, client, reader_token):
        """Test user can unsubscribe from newsletter."""
        # First subscribe
        client.post(
            "/newsletter/subscribe",
            headers={"Authorization": f"Bearer {reader_token}"},
            json={"frequency": "weekly"},
        )

        # Unsubscribe
        response = client.post(
            "/newsletter/unsubscribe", headers={"Authorization": f"Bearer {reader_token}"}
        )

        assert response.status_code == 200

    def test_newsletter_requires_auth(self, client):
        """Test newsletter endpoints require authentication."""
        response = client.post("/newsletter/subscribe", json={"frequency": "weekly"})

        assert response.status_code == 401
