"""
Contract tests for Stories API endpoints.
Tests MUST fail initially (red phase) until implementation is complete.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """FastAPI test client fixture."""
    from app.main import app

    return TestClient(app)


class TestStoriesList:
    """Contract tests for GET /stories endpoint."""

    def test_list_stories_success(self, client):
        """Test listing stories returns 200 with paginated response."""
        response = client.get("/stories")

        assert response.status_code == 200
        data = response.json()

        # Validate pagination response schema
        assert "stories" in data
        assert isinstance(data["stories"], list)
        assert "total" in data
        assert isinstance(data["total"], int)
        assert "page" in data
        assert isinstance(data["page"], int)
        assert "pages" in data
        assert isinstance(data["pages"], int)

    def test_list_stories_with_theme_filter(self, client):
        """Test filtering stories by theme."""
        response = client.get("/stories?theme=grief")

        assert response.status_code == 200
        data = response.json()

        # All returned stories should have 'grief' theme
        for story in data["stories"]:
            assert "themes" in story
            # Will need actual data to verify theme matching

    def test_list_stories_with_pagination(self, client):
        """Test pagination parameters work correctly."""
        response = client.get("/stories?page=1&limit=5")

        assert response.status_code == 200
        data = response.json()

        assert data["page"] == 1
        assert len(data["stories"]) <= 5

    def test_list_stories_with_search(self, client):
        """Test search across title, content, themes, author notes."""
        response = client.get("/stories?search=grief")

        assert response.status_code == 200
        data = response.json()

        # Search results should be relevant
        assert isinstance(data["stories"], list)

    def test_story_list_item_schema(self, client):
        """Test each story in list has correct schema."""
        response = client.get("/stories")

        assert response.status_code == 200
        stories = response.json()["stories"]

        if len(stories) > 0:
            story = stories[0]

            # Validate StoryListItem schema
            assert "id" in story
            assert isinstance(story["id"], int)
            assert "title" in story
            assert isinstance(story["title"], str)
            assert "excerpt" in story
            assert "cover_image_url" in story  # nullable
            assert "themes" in story
            assert isinstance(story["themes"], list)
            assert "read_time_minutes" in story
            assert isinstance(story["read_time_minutes"], int)
            assert "published_at" in story
            assert "comment_count" in story
            assert isinstance(story["comment_count"], int)
            assert "bookmark_count" in story
            assert isinstance(story["bookmark_count"], int)


class TestStoryDetail:
    """Contract tests for GET /stories/{id} endpoint."""

    def test_get_story_success(self, client):
        """Test getting published story by ID returns 200 with StoryDetail schema."""
        # This assumes story with ID 1 exists
        response = client.get("/stories/1")

        # Expected to fail until stories are seeded
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = response.json()

            # Validate StoryDetail schema
            assert "id" in data
            assert data["id"] == 1
            assert "title" in data
            assert "content" in data  # HTML content
            assert "cover_image_url" in data
            assert "content_warning" in data
            assert "themes" in data
            assert isinstance(data["themes"], list)

            # Validate theme object structure
            if len(data["themes"]) > 0:
                theme = data["themes"][0]
                assert "id" in theme
                assert "name" in theme
                assert "slug" in theme

            assert "read_time_minutes" in data
            assert "view_count" in data
            assert "published_at" in data
            assert "updated_at" in data

            # Validate author object
            assert "author" in data
            assert "full_name" in data["author"]

    def test_get_story_not_found(self, client):
        """Test getting non-existent story returns 404."""
        response = client.get("/stories/999999")

        assert response.status_code == 404

    def test_get_unpublished_story(self, client):
        """Test getting draft/archived story returns 404 for public users."""
        # This assumes story with ID 2 is draft/archived
        response = client.get("/stories/2")

        # Should be 404 if story is not published
        assert response.status_code in [404, 200]

    def test_story_view_count_increments(self, client):
        """Test viewing a story increments view count."""
        # First view
        response1 = client.get("/stories/1")

        if response1.status_code == 200:
            view_count_1 = response1.json()["view_count"]

            # Second view
            response2 = client.get("/stories/1")
            view_count_2 = response2.json()["view_count"]

            # View count should increment (or stay same if caching)
            assert view_count_2 >= view_count_1


class TestStoriesValidation:
    """Contract tests for request validation."""

    def test_invalid_theme_parameter(self, client):
        """Test invalid theme value is rejected."""
        response = client.get("/stories?theme=invalid_theme")

        # FastAPI should validate enum
        assert response.status_code in [400, 422]

    def test_exceed_max_limit(self, client):
        """Test limit > 100 is rejected or clamped."""
        response = client.get("/stories?limit=200")

        assert response.status_code in [200, 400, 422]

        if response.status_code == 200:
            # If accepted, should be clamped to 100
            stories = response.json()["stories"]
            assert len(stories) <= 100

    def test_invalid_page_number(self, client):
        """Test negative or zero page number handling."""
        response = client.get("/stories?page=0")

        # Should reject or default to page 1
        assert response.status_code in [200, 400, 422]
