"""
Lead capture API: anonymous newsletter signups + double opt-in flow.

Endpoints:
  POST /leads/subscribe    — capture email + UTMs, send confirmation
  GET  /leads/confirm      — click-through target, activates the lead + sends magnet
  POST /leads/unsubscribe  — revoke consent

Note: `from __future__ import annotations` is intentionally NOT used here.
Pydantic 2 + FastAPI's schema generation choke on forward-refs inside
slowapi-decorated handlers (all body models get stringified, breaking
TypeAdapter). Keep annotations concrete in this module.
"""

import json
import logging
import secrets
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Body, Depends, Header, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, EmailStr, Field
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_session
from app.models.lead_capture import LeadCapture
from app.models.lead_event import LeadEvent
from app.services import email as email_service
from app.services import posthog_server, sendgrid_webhook

logger = logging.getLogger(__name__)


def _frontend_base() -> str:
    """
    Return a scheme-qualified FRONTEND_URL. Defense-in-depth: if the env var
    is misconfigured (e.g. bare hostname from a stale .env), assume https.
    A RedirectResponse to a schemeless value is treated as relative by
    Starlette and produces open-redirect-looking URLs.
    """
    base = (settings.FRONTEND_URL or "").rstrip("/")
    if not base:
        return "http://localhost:5173"
    if not base.startswith(("http://", "https://")):
        return f"https://{base}"
    return base

router = APIRouter()

# Rate limit anonymous signups: 10/hr per IP. slowapi wires into request state.
limiter = Limiter(key_func=get_remote_address)

# Welcome sequence — 5 emails driven by an external scheduler (Cloud Scheduler
# in prod). Days between each event. SEQUENCE_INTERVALS_DAYS[0] is confirm→step 1;
# [i] for i>=1 is delay from step i → step i+1. Cumulative delivery from
# confirmation: day 2, 5, 9, 14, 19.
SEQUENCE_INTERVALS_DAYS: tuple[int, ...] = (2, 3, 4, 5, 5)
SEQUENCE_LAST_STEP = len(SEQUENCE_INTERVALS_DAYS)  # 5
SEQUENCE_BATCH_SIZE = 100


class UtmPayload(BaseModel):
    source: Optional[str] = Field(default=None, max_length=64)
    medium: Optional[str] = Field(default=None, max_length=64)
    campaign: Optional[str] = Field(default=None, max_length=128)
    content: Optional[str] = Field(default=None, max_length=128)
    term: Optional[str] = Field(default=None, max_length=128)


class SubscribeRequest(BaseModel):
    email: EmailStr
    source: str = Field(max_length=64)
    utm: Optional[UtmPayload] = None
    magnet_requested: bool = True
    referrer_url: Optional[str] = Field(default=None, max_length=500)


class SubscribeResponse(BaseModel):
    status: str


def _new_token() -> str:
    return secrets.token_urlsafe(32)


@router.post("/subscribe", response_model=SubscribeResponse, status_code=202)
@limiter.limit("10/hour")
async def subscribe(
    request: Request,  # noqa: ARG001  # required by slowapi
    background: BackgroundTasks,
    payload: SubscribeRequest = Body(...),
    session: AsyncSession = Depends(get_session),
) -> SubscribeResponse:
    """
    Idempotent on email — a re-subscribe rotates the token and re-sends confirmation
    (does NOT create a duplicate row). Confirmed leads that re-subscribe stay confirmed
    but still get a fresh confirmation link (useful if they lost it).
    """
    email_lc = payload.email.lower()
    existing = (
        await session.execute(select(LeadCapture).where(LeadCapture.email == email_lc))
    ).scalar_one_or_none()

    utm = payload.utm or UtmPayload()

    if existing is None:
        lead = LeadCapture(
            email=email_lc,
            source=payload.source,
            utm_source=utm.source,
            utm_medium=utm.medium,
            utm_campaign=utm.campaign,
            utm_content=utm.content,
            utm_term=utm.term,
            referrer_url=payload.referrer_url,
            magnet_requested=payload.magnet_requested,
            confirmation_token=_new_token(),
        )
        session.add(lead)
    else:
        existing.confirmation_token = _new_token()
        # Refresh attribution only if unconfirmed — don't rewrite history for
        # someone who already opted in.
        if existing.confirmed_at is None:
            existing.source = payload.source
            existing.utm_source = utm.source
            existing.utm_medium = utm.medium
            existing.utm_campaign = utm.campaign
            existing.utm_content = utm.content
            existing.utm_term = utm.term
            existing.referrer_url = payload.referrer_url
            existing.magnet_requested = payload.magnet_requested
        lead = existing

    await session.commit()
    await session.refresh(lead)

    # Fire email out-of-band so the client isn't blocked on SendGrid latency.
    background.add_task(email_service.send_confirmation, lead)

    return SubscribeResponse(status="pending_confirmation")


@router.get("/confirm")
async def confirm(
    background: BackgroundTasks,
    token: str = Query(..., min_length=8, max_length=128),
    session: AsyncSession = Depends(get_session),
) -> RedirectResponse:
    """Click-through target from the confirmation email. Sets confirmed_at, sends magnet."""
    lead = (
        await session.execute(select(LeadCapture).where(LeadCapture.confirmation_token == token))
    ).scalar_one_or_none()

    if lead is None:
        raise HTTPException(status_code=404, detail="Confirmation link is invalid or has expired.")

    already_confirmed = lead.confirmed_at is not None
    if not already_confirmed:
        lead.confirmed_at = datetime.utcnow()
        # Schedule welcome sequence step 1. SEQUENCE_INTERVALS_DAYS[0] is the
        # delay from confirmation → step 1; subsequent indices drive the tick.
        lead.next_send_at = datetime.utcnow() + timedelta(days=SEQUENCE_INTERVALS_DAYS[0])
        lead.sequence_step = 0
        lead.unsubscribed_at = None  # in case they'd unsubscribed and now re-opted-in

        await session.commit()

    # Send the magnet whether first-time or re-request — user clicked the link, honor it.
    background.add_task(email_service.send_magnet, lead)

    redirect_url = f"{_frontend_base()}/subscribed?magnet=1"
    return RedirectResponse(url=redirect_url, status_code=302)


@router.post("/unsubscribe")
async def unsubscribe(
    token: str = Query(..., min_length=8, max_length=128),
    session: AsyncSession = Depends(get_session),
) -> dict[str, str]:
    lead = (
        await session.execute(select(LeadCapture).where(LeadCapture.confirmation_token == token))
    ).scalar_one_or_none()
    if lead is None:
        raise HTTPException(status_code=404, detail="Unknown token.")

    lead.unsubscribed_at = datetime.utcnow()
    await session.commit()
    return {"status": "unsubscribed"}


class TickResponse(BaseModel):
    processed: int
    completed: int  # rows that advanced past the last step (sequence done)


def _verify_scheduler_token(header_value: Optional[str]) -> None:
    """Header-based auth for the tick endpoint. Rejects if SCHEDULER_TOKEN is
    unset (never accept unauth in prod) or if the header doesn't match."""
    expected = settings.SCHEDULER_TOKEN
    if not expected:
        logger.error("Tick request rejected: SCHEDULER_TOKEN is not configured.")
        raise HTTPException(status_code=503, detail="Sequence scheduler not configured.")
    if not header_value or not secrets.compare_digest(header_value, expected):
        raise HTTPException(status_code=401, detail="Invalid scheduler token.")


@router.post("/sequence/tick", response_model=TickResponse)
async def sequence_tick(
    x_scheduler_token: Optional[str] = Header(default=None, alias="X-Scheduler-Token"),
    session: AsyncSession = Depends(get_session),
) -> TickResponse:
    """
    Advance the welcome sequence for up to SEQUENCE_BATCH_SIZE due leads.

    Cloud Scheduler hits this every ~15 minutes. Each row is locked with
    FOR UPDATE SKIP LOCKED so parallel workers don't step on each other; the
    send + state update happen in the same transaction so a crash mid-batch
    is safe to retry (worst case a lead skips a scheduled slot by 15 min).
    """
    _verify_scheduler_token(x_scheduler_token)

    now = datetime.utcnow()

    stmt = (
        select(LeadCapture)
        .where(LeadCapture.confirmed_at.is_not(None))
        .where(LeadCapture.unsubscribed_at.is_(None))
        .where(LeadCapture.next_send_at.is_not(None))
        .where(LeadCapture.next_send_at <= now)
        .where(LeadCapture.sequence_step < SEQUENCE_LAST_STEP)
        .order_by(LeadCapture.next_send_at.asc())
        .limit(SEQUENCE_BATCH_SIZE)
        .with_for_update(skip_locked=True)
    )
    rows = (await session.execute(stmt)).scalars().all()

    processed = 0
    completed = 0
    for lead in rows:
        next_step = (lead.sequence_step or 0) + 1
        if next_step < 1 or next_step > SEQUENCE_LAST_STEP:
            continue

        # Send synchronously inside the transaction — if SendGrid raises the
        # rollback keeps the row eligible for retry on the next tick.
        # `send_sequence_step` swallows its own errors and returns bool; we log
        # a warning on False but still advance the state, because getting stuck
        # on a permanent SendGrid failure (bad address, suppressed) would keep
        # the same lead at the head of the queue forever.
        ok = email_service.send_sequence_step(lead, next_step)
        if not ok:
            logger.warning(
                "sequence_tick: send_sequence_step returned False for lead %s step %s",
                lead.email,
                next_step,
            )

        lead.sequence_step = next_step
        if next_step >= SEQUENCE_LAST_STEP:
            lead.next_send_at = None
            completed += 1
        else:
            # Interval BEFORE the NEXT step. next_step is 1-indexed and we've
            # just delivered it; next interval is SEQUENCE_INTERVALS_DAYS[next_step].
            days = SEQUENCE_INTERVALS_DAYS[next_step]
            lead.next_send_at = now + timedelta(days=days)
        processed += 1

    await session.commit()
    logger.info("sequence_tick: processed=%s completed=%s", processed, completed)
    return TickResponse(processed=processed, completed=completed)


# ─────────────────────────────────────────────────────────────────────────────
# SendGrid Event Webhook.
#
# SendGrid POSTs a batch of events per delivery — up to hundreds per request
# with a max ~30s attempt window. We persist each interesting one to
# `lead_event` (unique on sg_event_id → idempotent to redelivery) and mirror
# `open` events into PostHog so the Tier 4 funnel dashboard has server-side
# confirmation-open data joined to the client-side signup event.
# ─────────────────────────────────────────────────────────────────────────────

# Event types we actually care about persisting. SendGrid delivers many more
# (processed, deferred, etc.) — filter aggressively to keep the table small.
_TRACKED_EVENT_TYPES = frozenset(
    {"delivered", "open", "click", "bounce", "spamreport", "unsubscribe", "dropped"}
)


class WebhookResponse(BaseModel):
    accepted: int
    skipped: int


@router.post("/sendgrid/webhook", response_model=WebhookResponse)
async def sendgrid_webhook_receiver(
    request: Request,
    session: AsyncSession = Depends(get_session),
    x_signature: Optional[str] = Header(
        default=None, alias="X-Twilio-Email-Event-Webhook-Signature"
    ),
    x_timestamp: Optional[str] = Header(
        default=None, alias="X-Twilio-Email-Event-Webhook-Timestamp"
    ),
) -> WebhookResponse:
    """
    Receive a SendGrid Event Webhook batch. Verifies the ECDSA signature,
    upserts per-event rows into lead_event (idempotent), and forwards `open`
    events to PostHog as `confirmation_email_opened`.
    """
    if not settings.SENDGRID_WEBHOOK_PUBLIC_KEY:
        logger.error("Webhook rejected: SENDGRID_WEBHOOK_PUBLIC_KEY not configured.")
        raise HTTPException(status_code=503, detail="Webhook not configured.")

    raw_body = await request.body()
    if not sendgrid_webhook.verify(x_signature, x_timestamp, raw_body):
        raise HTTPException(status_code=401, detail="Signature verification failed.")

    try:
        events = json.loads(raw_body.decode("utf-8"))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body.")

    if not isinstance(events, list):
        raise HTTPException(status_code=400, detail="Body must be a JSON array.")

    accepted = 0
    skipped = 0
    for event in events:
        if not isinstance(event, dict):
            skipped += 1
            continue
        event_type = str(event.get("event", "")).lower()
        sg_event_id = str(event.get("sg_event_id", ""))
        email_addr = str(event.get("email", "")).lower()

        if event_type not in _TRACKED_EVENT_TYPES or not sg_event_id or not email_addr:
            skipped += 1
            continue

        # Locate the lead — skip events for addresses we don't track (e.g. sent
        # to a manual test address outside the funnel).
        lead = (
            await session.execute(select(LeadCapture).where(LeadCapture.email == email_addr))
        ).scalar_one_or_none()
        if lead is None:
            skipped += 1
            continue

        # Idempotent insert. Race: two concurrent workers processing the same
        # batch would both try to insert; unique constraint on sg_event_id
        # catches it — we swallow the integrity error and count as accepted.
        try:
            audit = LeadEvent(
                lead_id=lead.id,
                event_type=event_type,
                sg_event_id=sg_event_id,
                payload_json=json.dumps(event),
            )
            session.add(audit)
            await session.flush()
        except Exception as exc:  # sqlalchemy IntegrityError bubbles as generic here
            # Roll the failed flush back but keep processing the rest of the batch.
            await session.rollback()
            logger.debug("Skipping duplicate sg_event_id=%s (%s)", sg_event_id, exc)
            skipped += 1
            continue

        # Mirror opens into PostHog for the funnel dashboard.
        if event_type == "open":
            posthog_server.capture(
                posthog_server.hash_email(email_addr),
                "confirmation_email_opened",
                {
                    "source": lead.source,
                    "utm_source": lead.utm_source,
                    "utm_medium": lead.utm_medium,
                    "utm_campaign": lead.utm_campaign,
                },
            )
        accepted += 1

    await session.commit()
    return WebhookResponse(accepted=accepted, skipped=skipped)
