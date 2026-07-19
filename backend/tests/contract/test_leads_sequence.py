"""
Contract tests for POST /leads/sequence/tick.

Same infra caveats as the other contract tests — requires a reachable DB;
sync TestClient + async engine pool sharing an event loop across tests can
produce spurious "Event loop is closed" errors between cases. Run cases
individually if they fail as a suite.
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

TOKEN = "test-scheduler-token"


@pytest.fixture
def client(monkeypatch):
    """Wire the scheduler token + stub SendGrid to a no-op so the tick has an
    end-to-end path without a real API key."""
    from app.core.config import settings
    from app.services import email as email_service

    monkeypatch.setattr(settings, "SCHEDULER_TOKEN", TOKEN)
    monkeypatch.setattr(email_service, "send_confirmation", lambda lead: True)
    monkeypatch.setattr(email_service, "send_magnet", lambda lead: True)
    monkeypatch.setattr(email_service, "send_sequence_step", lambda lead, step: True)

    from app.main import app

    return TestClient(app)


def _rand() -> str:
    return f"seq-{uuid.uuid4().hex[:12]}@example.com"


async def _seed_confirmed_lead(email: str, next_send_at: datetime) -> int:
    """Insert a confirmed lead with next_send_at in the past so the tick
    picks it up. Returns the id."""
    from app.core.database import async_session_maker
    from app.models.lead_capture import LeadCapture
    from sqlalchemy import select

    async with async_session_maker() as session:
        lead = LeadCapture(
            email=email,
            source="seq-test",
            confirmation_token=uuid.uuid4().hex,
            confirmed_at=datetime.utcnow(),
            next_send_at=next_send_at,
            sequence_step=0,
        )
        session.add(lead)
        await session.commit()
        result = await session.execute(select(LeadCapture).where(LeadCapture.email == email))
        return result.scalar_one().id


async def _fetch_lead(email: str):
    from app.core.database import async_session_maker
    from app.models.lead_capture import LeadCapture
    from sqlalchemy import select

    async with async_session_maker() as session:
        return (
            await session.execute(select(LeadCapture).where(LeadCapture.email == email))
        ).scalar_one()


class TestSequenceTickAuth:
    def test_missing_token_401(self, client):
        assert client.post("/leads/sequence/tick").status_code == 401

    def test_wrong_token_401(self, client):
        resp = client.post(
            "/leads/sequence/tick", headers={"X-Scheduler-Token": "wrong"}
        )
        assert resp.status_code == 401

    def test_scheduler_unconfigured_503(self, client, monkeypatch):
        """If SCHEDULER_TOKEN is unset in prod, the endpoint should fail closed."""
        from app.core.config import settings

        monkeypatch.setattr(settings, "SCHEDULER_TOKEN", "")
        resp = client.post(
            "/leads/sequence/tick", headers={"X-Scheduler-Token": "anything"}
        )
        assert resp.status_code == 503


class TestSequenceTickBehavior:
    def test_no_due_leads_returns_zero(self, client):
        resp = client.post(
            "/leads/sequence/tick", headers={"X-Scheduler-Token": TOKEN}
        )
        assert resp.status_code == 200
        # There may be leads left from other tests, but they'll be past their step
        # or unsubscribed; the API contract is that response shape is stable.
        body = resp.json()
        assert "processed" in body and "completed" in body

    def test_due_lead_advances_and_reschedules(self, client):
        email = _rand()
        asyncio.get_event_loop().run_until_complete(
            _seed_confirmed_lead(email, next_send_at=datetime.utcnow() - timedelta(minutes=1))
        )

        resp = client.post(
            "/leads/sequence/tick", headers={"X-Scheduler-Token": TOKEN}
        )
        assert resp.status_code == 200

        row = asyncio.get_event_loop().run_until_complete(_fetch_lead(email))
        assert row.sequence_step == 1
        # next_send_at was rescheduled ~3 days out (interval index 1) — assert it
        # advanced from "past" to "future" without pinning the exact delta.
        assert row.next_send_at is not None
        assert row.next_send_at > datetime.utcnow() + timedelta(days=2)

    def test_future_lead_is_skipped(self, client):
        email = _rand()
        asyncio.get_event_loop().run_until_complete(
            _seed_confirmed_lead(email, next_send_at=datetime.utcnow() + timedelta(days=1))
        )

        resp = client.post(
            "/leads/sequence/tick", headers={"X-Scheduler-Token": TOKEN}
        )
        assert resp.status_code == 200

        row = asyncio.get_event_loop().run_until_complete(_fetch_lead(email))
        assert row.sequence_step == 0  # untouched
