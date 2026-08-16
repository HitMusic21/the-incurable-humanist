"""
Thin server-side PostHog wrapper. Same shape as services/email.py — safe no-op
when POSTHOG_API_KEY is unset (local dev, CI) so calling code doesn't need to
guard every capture.
"""

from __future__ import annotations

import hashlib
import logging
from typing import Any

import posthog

from app.core.config import settings

logger = logging.getLogger(__name__)

_initialized = False


def _init_once() -> bool:
    global _initialized
    if _initialized:
        return True
    if not settings.POSTHOG_API_KEY:
        return False
    # Client-side and server-side PostHog use the same project API key.
    posthog.api_key = settings.POSTHOG_API_KEY
    posthog.host = settings.POSTHOG_HOST or "https://us.i.posthog.com"
    _initialized = True
    return True


def hash_email(email: str) -> str:
    """Stable distinct_id from email — SHA-256, lowercased, no salt (we want the
    same id on client and server so events join up in PostHog)."""
    return "email:" + hashlib.sha256(email.strip().lower().encode("utf-8")).hexdigest()


def capture(distinct_id: str, event: str, properties: dict[str, Any] | None = None) -> bool:
    """Fire-and-forget capture. Returns True on enqueue, False on no-op or error."""
    if not _init_once():
        logger.debug("posthog no-op: POSTHOG_API_KEY unset (event=%s)", event)
        return False
    try:
        posthog.capture(distinct_id, event=event, properties=properties or {})
        return True
    except Exception:
        logger.exception("posthog.capture failed for event=%s", event)
        return False


def alias(distinct_id: str, alias_id: str) -> bool:
    """Alias a server-side distinct_id to a client-side one. Used when a
    confirmed lead lands on /subscribed — the redirect can carry the hashed-email
    distinct_id in a param and we alias it to whatever the anon client id was."""
    if not _init_once():
        return False
    try:
        posthog.alias(previous_id=distinct_id, distinct_id=alias_id)
        return True
    except Exception:
        logger.exception("posthog.alias failed")
        return False
