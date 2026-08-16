"""
Contract tests for /stories/* against the shipped Sprint 2 implementation.

Was previously two files (a spec-driven skeleton + a `*_impl.py` shadow). The
spec version specified a richer feature set (theme filtering, search,
page-based pagination, comment/bookmark counts on list items) that never
shipped — those endpoints belong to the deferred reader-engagement surface
(see the skip notice in test_reader_api.py). This is now the single canonical
stories contract test.

Requires a reachable DB (docker-compose db). The autouse fixtures in
conftest.py truncate mutable tables between tests + override get_session
with a NullPool async engine to keep asyncpg from bleeding between loops.
"""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient


def _rand(prefix: str = "seg") -> str:
    return f"{prefix}-{uuid.uuid4().hex[:10]}"


@pytest.fixture
def client():
    from app.main import app

    return TestClient(app)


@pytest.fixture
def author_token(client) -> str:
    """Register the author (or reuse if the row already exists) and return a token."""
    from app.core.config import settings

    email = settings.AUTHOR_EMAIL
    password = "TestPass12345"

    client.post(
        "/auth/register",
        json={"email": email, "password": password, "full_name": "Test Author"},
    )
    login = client.post("/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200, login.text
    return login.json()["access_token"]


class TestPublicStories:
    def test_list_returns_shape(self, client):
        resp = client.get("/stories")
        assert resp.status_code == 200
        body = resp.json()
        assert "stories" in body and "total_count" in body

    def test_get_unknown_slug_404(self, client):
        assert client.get(f"/stories/{_rand('nope')}").status_code == 404


class TestAuthoredMutation:
    def test_create_requires_author(self, client):
        resp = client.post(
            "/stories",
            json={"title": "Anon Attempt", "content": "<p>x</p>"},
        )
        # HTTPBearer without a token returns 403 (not 401) — see test_auth_api
        # for the same convention.
        assert resp.status_code in (401, 403)

    def test_full_crud_lifecycle(self, client, author_token):
        headers = {"Authorization": f"Bearer {author_token}"}
        title = f"Contract Essay {_rand('c')}"

        created = client.post(
            "/stories",
            headers=headers,
            json={
                "title": title,
                "content": "<p>Body.</p>",
                "meta_description": "meta",
            },
        )
        assert created.status_code == 201, created.text
        c = created.json()
        assert c["slug"]  # auto-generated from title
        assert c["status"] == "draft"
        assert c["published_at"] is None
        story_id = c["id"]
        slug = c["slug"]

        # Draft is not publicly visible.
        assert client.get(f"/stories/{slug}").status_code == 404

        # Publish it.
        patched = client.patch(
            f"/stories/{story_id}",
            headers=headers,
            json={"status": "published"},
        )
        assert patched.status_code == 200
        p = patched.json()
        assert p["status"] == "published"
        assert p["published_at"] is not None

        # Public GET now returns it + increments view_count on each read.
        first = client.get(f"/stories/{slug}").json()
        second = client.get(f"/stories/{slug}").json()
        assert second["view_count"] == first["view_count"] + 1

        # Delete.
        assert client.delete(f"/stories/{story_id}", headers=headers).status_code == 204
        assert client.get(f"/stories/{slug}").status_code == 404

    def test_slug_collision_gets_suffix(self, client, author_token):
        headers = {"Authorization": f"Bearer {author_token}"}
        title = f"Same Title {_rand('s')}"
        first = client.post(
            "/stories", headers=headers, json={"title": title, "content": "<p>a</p>"}
        ).json()
        second = client.post(
            "/stories", headers=headers, json={"title": title, "content": "<p>b</p>"}
        ).json()
        assert first["slug"] != second["slug"]
        assert second["slug"].startswith(first["slug"] + "-")

    def test_admin_get_by_id_returns_drafts(self, client, author_token):
        """Public GET /stories/{slug} hides drafts (404). Admin GET /stories/id/{id}
        returns them — that's how the editor hydrates a draft."""
        headers = {"Authorization": f"Bearer {author_token}"}
        created = client.post(
            "/stories", headers=headers, json={"title": _rand("d"), "content": "<p>d</p>"}
        ).json()
        assert client.get(f"/stories/{created['slug']}").status_code == 404
        resp = client.get(f"/stories/id/{created['id']}", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["slug"] == created["slug"]
