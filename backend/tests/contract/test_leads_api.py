"""
Contract tests for /leads/* — anonymous newsletter capture + double opt-in.

Requires a reachable database (same pattern as the other contract tests).
Email delivery is patched out; we only assert on API contract + DB state.
"""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient


def unique_email() -> str:
    return f"lead-{uuid.uuid4().hex[:12]}@example.com"


@pytest.fixture
def client(monkeypatch):
    """FastAPI test client with SendGrid stubbed to a no-op."""
    from app.services import email as email_service

    monkeypatch.setattr(email_service, "send_confirmation", lambda lead: True)
    monkeypatch.setattr(email_service, "send_magnet", lambda lead: True)
    monkeypatch.setattr(email_service, "send_sequence_step", lambda lead, step: True)

    from app.main import app

    return TestClient(app)


class TestSubscribe:
    def test_subscribe_success(self, client):
        response = client.post(
            "/leads/subscribe",
            json={
                "email": unique_email(),
                "source": "home-hero",
                "magnet_requested": True,
                "utm": {
                    "source": "instagram",
                    "medium": "organic-social",
                    "campaign": "spring-arc",
                },
            },
        )
        assert response.status_code == 202
        assert response.json() == {"status": "pending_confirmation"}

    def test_subscribe_rejects_invalid_email(self, client):
        response = client.post(
            "/leads/subscribe",
            json={"email": "not-an-email", "source": "home-hero"},
        )
        assert response.status_code == 422

    def test_subscribe_is_idempotent_on_email(self, client):
        """Re-subscribing with the same email must not 500; it rotates the token."""
        email = unique_email()
        first = client.post(
            "/leads/subscribe",
            json={"email": email, "source": "home-hero"},
        )
        assert first.status_code == 202
        second = client.post(
            "/leads/subscribe",
            json={"email": email, "source": "exit-intent"},
        )
        assert second.status_code == 202


class TestConfirm:
    def test_confirm_flow_end_to_end(self, client):
        """
        Full happy path: subscribe → look up the stored token → GET /confirm →
        302 redirect to /subscribed?magnet=1 with confirmed_at populated.
        """
        import asyncio

        from app.core.database import async_session_maker
        from app.models.lead_capture import LeadCapture
        from sqlalchemy import select

        email = unique_email()
        subscribe = client.post(
            "/leads/subscribe", json={"email": email, "source": "home-hero"}
        )
        assert subscribe.status_code == 202

        async def fetch_token() -> str:
            async with async_session_maker() as s:
                row = (
                    await s.execute(select(LeadCapture).where(LeadCapture.email == email))
                ).scalar_one()
                return row.confirmation_token

        token = asyncio.get_event_loop().run_until_complete(fetch_token())

        resp = client.get(f"/leads/confirm?token={token}", follow_redirects=False)
        assert resp.status_code == 302
        assert "/subscribed?magnet=1" in resp.headers["location"]

        async def fetch_confirmed_at():
            async with async_session_maker() as s:
                row = (
                    await s.execute(select(LeadCapture).where(LeadCapture.email == email))
                ).scalar_one()
                return row.confirmed_at

        confirmed_at = asyncio.get_event_loop().run_until_complete(fetch_confirmed_at())
        assert confirmed_at is not None

    def test_confirm_unknown_token_returns_404(self, client):
        resp = client.get("/leads/confirm?token=notavalidtoken12345")
        assert resp.status_code == 404


class TestUnsubscribe:
    def test_unknown_token_returns_404(self, client):
        resp = client.post("/leads/unsubscribe?token=doesnotexist12345")
        assert resp.status_code == 404
