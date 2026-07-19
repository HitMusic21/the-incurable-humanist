"""
Contract tests for POST /leads/sendgrid/webhook.

Uses a generated ECDSA P-256 keypair per test — the public key is stuffed into
`settings.SENDGRID_WEBHOOK_PUBLIC_KEY` and we sign requests with the matching
private key.
"""

from __future__ import annotations

import asyncio
import base64
import json
import uuid
from datetime import datetime

import pytest
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi.testclient import TestClient


def _generate_keypair() -> tuple[ec.EllipticCurvePrivateKey, str]:
    """Return (private_key, public_key_pem_str). Public PEM matches what
    SENDGRID_WEBHOOK_PUBLIC_KEY expects."""
    private_key = ec.generate_private_key(ec.SECP256R1())
    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("ascii")
    return private_key, public_pem


def _sign(private_key: ec.EllipticCurvePrivateKey, timestamp: str, body: bytes) -> str:
    signature = private_key.sign(timestamp.encode("utf-8") + body, ec.ECDSA(hashes.SHA256()))
    return base64.b64encode(signature).decode("ascii")


@pytest.fixture
def signing_key(monkeypatch):
    from app.core.config import settings

    private_key, public_pem = _generate_keypair()
    monkeypatch.setattr(settings, "SENDGRID_WEBHOOK_PUBLIC_KEY", public_pem)
    return private_key


@pytest.fixture
def client(signing_key, monkeypatch):
    """Wire signing key + stub server-side PostHog + stub SendGrid send fns."""
    from app.services import email as email_service
    from app.services import posthog_server

    monkeypatch.setattr(email_service, "send_confirmation", lambda lead: True)
    monkeypatch.setattr(email_service, "send_magnet", lambda lead: True)
    monkeypatch.setattr(email_service, "send_sequence_step", lambda lead, step: True)
    monkeypatch.setattr(posthog_server, "capture", lambda distinct_id, event, properties=None: True)

    from app.main import app

    return TestClient(app)


async def _seed_lead(email: str) -> int:
    from app.core.database import async_session_maker
    from app.models.lead_capture import LeadCapture

    async with async_session_maker() as session:
        lead = LeadCapture(
            email=email,
            source="webhook-test",
            confirmation_token=uuid.uuid4().hex,
            confirmed_at=datetime.utcnow(),
        )
        session.add(lead)
        await session.commit()
        return lead.id


async def _count_events(sg_event_id: str) -> int:
    from sqlalchemy import func, select

    from app.core.database import async_session_maker
    from app.models.lead_event import LeadEvent

    async with async_session_maker() as session:
        result = await session.execute(
            select(func.count()).select_from(LeadEvent).where(LeadEvent.sg_event_id == sg_event_id)
        )
        return result.scalar_one()


class TestWebhookAuth:
    def test_missing_public_key_returns_503(self, client, monkeypatch):
        """If SENDGRID_WEBHOOK_PUBLIC_KEY is unset, fail closed."""
        from app.core.config import settings

        monkeypatch.setattr(settings, "SENDGRID_WEBHOOK_PUBLIC_KEY", "")
        resp = client.post("/leads/sendgrid/webhook", json=[])
        assert resp.status_code == 503

    def test_missing_signature_returns_401(self, client):
        resp = client.post("/leads/sendgrid/webhook", json=[])
        assert resp.status_code == 401

    def test_wrong_signature_returns_401(self, client):
        body = json.dumps([]).encode("utf-8")
        resp = client.post(
            "/leads/sendgrid/webhook",
            content=body,
            headers={
                "X-Twilio-Email-Event-Webhook-Signature": base64.b64encode(b"nope" * 16).decode(),
                "X-Twilio-Email-Event-Webhook-Timestamp": "1700000000",
                "Content-Type": "application/json",
            },
        )
        assert resp.status_code == 401


class TestWebhookAccept:
    def test_valid_signature_persists_and_is_idempotent(self, client, signing_key):
        email = f"wh-{uuid.uuid4().hex[:8]}@example.com"
        asyncio.get_event_loop().run_until_complete(_seed_lead(email))
        sg_event_id = f"sg-{uuid.uuid4().hex}"
        events = [
            {
                "event": "open",
                "email": email,
                "sg_event_id": sg_event_id,
                "timestamp": 1700000000,
            }
        ]
        body = json.dumps(events).encode("utf-8")
        timestamp = "1700000000"
        signature = _sign(signing_key, timestamp, body)
        headers = {
            "X-Twilio-Email-Event-Webhook-Signature": signature,
            "X-Twilio-Email-Event-Webhook-Timestamp": timestamp,
            "Content-Type": "application/json",
        }

        first = client.post("/leads/sendgrid/webhook", content=body, headers=headers)
        assert first.status_code == 200, first.text
        assert first.json() == {"accepted": 1, "skipped": 0}

        # Replay: SendGrid may re-deliver the same batch. sg_event_id is unique →
        # the second call should skip everything.
        second = client.post("/leads/sendgrid/webhook", content=body, headers=headers)
        assert second.status_code == 200
        assert second.json() == {"accepted": 0, "skipped": 1}

        # Audit row present exactly once.
        count = asyncio.get_event_loop().run_until_complete(_count_events(sg_event_id))
        assert count == 1

    def test_skips_events_for_unknown_addresses(self, client, signing_key):
        events = [
            {
                "event": "open",
                "email": "not-in-our-db@example.com",
                "sg_event_id": f"sg-{uuid.uuid4().hex}",
                "timestamp": 1700000000,
            }
        ]
        body = json.dumps(events).encode("utf-8")
        signature = _sign(signing_key, "1700000000", body)
        resp = client.post(
            "/leads/sendgrid/webhook",
            content=body,
            headers={
                "X-Twilio-Email-Event-Webhook-Signature": signature,
                "X-Twilio-Email-Event-Webhook-Timestamp": "1700000000",
                "Content-Type": "application/json",
            },
        )
        assert resp.status_code == 200
        assert resp.json() == {"accepted": 0, "skipped": 1}
