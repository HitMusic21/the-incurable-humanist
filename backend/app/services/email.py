"""
SendGrid transactional email service.

Owns three flows: confirmation (double opt-in), lead-magnet delivery, and the
5-step welcome sequence. All send calls are safe no-ops in environments where
SENDGRID_API_KEY is unset (local dev, CI) — they log and return False rather
than raise, so the calling code stays simple.
"""

from __future__ import annotations

import logging
from typing import Any

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from app.core.config import settings
from app.models.lead_capture import LeadCapture

logger = logging.getLogger(__name__)


def _client() -> SendGridAPIClient | None:
    if not settings.SENDGRID_API_KEY:
        return None
    return SendGridAPIClient(settings.SENDGRID_API_KEY)


def _send(template_id: str, to_email: str, dynamic_data: dict[str, Any]) -> bool:
    """Dispatch a dynamic-template email. Returns True on 2xx, False otherwise (or on no-op)."""
    client = _client()
    if client is None:
        logger.warning(
            "SendGrid no-op: SENDGRID_API_KEY unset. Would have sent template=%s to=%s data=%s",
            template_id,
            to_email,
            dynamic_data,
        )
        return False
    if not template_id:
        logger.error("SendGrid send skipped: template_id is empty (check SENDGRID_TPL_* env vars)")
        return False

    message = Mail(
        from_email=(settings.SENDGRID_FROM_EMAIL, settings.SENDGRID_FROM_NAME),
        to_emails=to_email,
    )
    message.template_id = template_id
    message.dynamic_template_data = dynamic_data

    try:
        response = client.send(message)
    except Exception:
        logger.exception("SendGrid send failed for template=%s to=%s", template_id, to_email)
        return False

    ok = 200 <= response.status_code < 300
    if not ok:
        logger.error(
            "SendGrid non-2xx: status=%s template=%s to=%s body=%s",
            response.status_code,
            template_id,
            to_email,
            response.body,
        )
    return ok


def _frontend_base() -> str:
    """Same normalization as app.api.leads — kept local to avoid a circular import."""
    base = (settings.FRONTEND_URL or "").rstrip("/")
    if not base:
        return "http://localhost:5173"
    if not base.startswith(("http://", "https://")):
        return f"https://{base}"
    return base


def _confirm_url(lead: LeadCapture) -> str:
    return f"{_frontend_base()}/leads/confirm?token={lead.confirmation_token}"


def _unsubscribe_url(lead: LeadCapture) -> str:
    return f"{_frontend_base()}/leads/unsubscribe?token={lead.confirmation_token}"


def _magnet_url(lead: LeadCapture) -> str:
    base = settings.MAGNET_PDF_URL
    if base.startswith("http"):
        return f"{base}?t={lead.confirmation_token}"
    return f"{_frontend_base()}{base}?t={lead.confirmation_token}"


def send_confirmation(lead: LeadCapture) -> bool:
    """Double opt-in confirmation email with a click-to-confirm link."""
    return _send(
        settings.SENDGRID_TPL_CONFIRM,
        lead.email,
        {
            "confirm_url": _confirm_url(lead),
            "unsubscribe_url": _unsubscribe_url(lead),
            "source": lead.source,
        },
    )


def send_magnet(lead: LeadCapture) -> bool:
    """Delivers the 5-essay starter reader PDF after confirmation."""
    return _send(
        settings.SENDGRID_TPL_MAGNET,
        lead.email,
        {
            "magnet_url": _magnet_url(lead),
            "unsubscribe_url": _unsubscribe_url(lead),
        },
    )


_SEQUENCE_TEMPLATES = {
    1: lambda: settings.SENDGRID_TPL_SEQ_1,
    2: lambda: settings.SENDGRID_TPL_SEQ_2,
    3: lambda: settings.SENDGRID_TPL_SEQ_3,
    4: lambda: settings.SENDGRID_TPL_SEQ_4,
    5: lambda: settings.SENDGRID_TPL_SEQ_5,
}


def send_sequence_step(lead: LeadCapture, step: int) -> bool:
    """Send one step (1..5) of the welcome sequence. Wired to Cloud Scheduler in Tier 3."""
    resolver = _SEQUENCE_TEMPLATES.get(step)
    if resolver is None:
        logger.error("Invalid sequence step %s for lead %s", step, lead.email)
        return False
    return _send(
        resolver(),
        lead.email,
        {"unsubscribe_url": _unsubscribe_url(lead), "step": step},
    )
