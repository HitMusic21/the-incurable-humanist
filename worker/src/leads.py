"""Lead capture — newsletter signup + double opt-in, ported to D1.

Ported from backend/app/api/leads.py. Behaviour preserved:

  - Idempotent on email. A re-subscribe rotates the confirmation token and
    re-sends the email; it never creates a duplicate row.
  - Attribution (source/UTMs/referrer) is refreshed only while the lead is
    UNCONFIRMED — we don't rewrite history for someone who already opted in.
  - Confirmation is a GET click-through that sets confirmed_at and redirects
    to the frontend.

Differences forced by the Workers runtime:
  - The SendGrid SDK is replaced by a direct httpx call to its REST API. It is
    a plain HTTP endpoint, and the SDK pulls in far more than a Worker needs.
  - Sends are awaited inline rather than via BackgroundTasks. A Worker's
    lifetime ends with the response, so a fire-and-forget task can be killed
    mid-flight; SendGrid is fast and a failure must not fail the signup, so
    send errors are swallowed and logged (same net effect as the old
    background task failing silently).
  - No slowapi rate limiter. Cloudflare's own rate limiting sits in front of
    the Worker; see the note on `subscribe`.
"""

from __future__ import annotations

import secrets
from datetime import datetime, timezone

import httpx

SENDGRID_URL = "https://api.sendgrid.com/v3/mail/send"


def _now_iso() -> str:
    """UTC timestamp as strict ISO 8601 with a 'Z' offset, matching
    substack_sync so every table stores one consistent format."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def new_token() -> str:
    return secrets.token_urlsafe(32)


async def _query(db, sql: str, *params) -> list[dict]:
    stmt = db.prepare(sql)
    if params:
        stmt = stmt.bind(*params)
    result = await stmt.all()
    rows = result.results
    rows = rows.to_py() if hasattr(rows, "to_py") else rows
    out = []
    for row in rows:
        row = row.to_py() if hasattr(row, "to_py") else row
        out.append(dict(row) if not isinstance(row, dict) else row)
    return out


async def _run(db, sql: str, *params) -> None:
    stmt = db.prepare(sql)
    if params:
        stmt = stmt.bind(*params)
    await stmt.run()


async def send_confirmation(settings: dict, email: str, token: str) -> bool:
    """Send the double opt-in email.

    Returns False (never raises) when SENDGRID_API_KEY or the template id is
    unset — local dev and CI run without them, and a missing key must not turn
    a successful signup into a 500.
    """
    api_key = settings.get("SENDGRID_API_KEY")
    template_id = settings.get("SENDGRID_TPL_CONFIRM")
    if not api_key or not template_id:
        print(f"SendGrid no-op (key/template unset): would confirm {email}")
        return False

    base = (settings.get("FRONTEND_URL") or "https://theincurablehumanist.com").rstrip("/")
    payload = {
        "from": {
            "email": settings.get("SENDGRID_FROM_EMAIL", "hello@theincurablehumanist.com"),
            "name": settings.get("SENDGRID_FROM_NAME", "Denise Rodriguez Dao"),
        },
        "personalizations": [
            {
                "to": [{"email": email}],
                "dynamic_template_data": {
                    "confirm_url": f"{base}/api/leads/confirm?token={token}",
                },
            }
        ],
        "template_id": template_id,
    }
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                SENDGRID_URL,
                json=payload,
                headers={"Authorization": f"Bearer {api_key}"},
            )
        if resp.status_code >= 300:
            print(f"SendGrid send failed {resp.status_code}: {resp.text[:200]}")
            return False
        return True
    except Exception as exc:  # noqa: BLE001 - a mail failure must not fail signup
        print(f"SendGrid send errored: {type(exc).__name__}: {exc}")
        return False


async def subscribe(db, settings: dict, payload: dict) -> dict:
    """Capture an email + attribution and send the confirmation.

    Idempotent on email: an existing row has its token rotated rather than a
    second row inserted (email is UNIQUE, so an INSERT would fail anyway).
    """
    email_lc = (payload.get("email") or "").strip().lower()
    if not email_lc or "@" not in email_lc:
        raise ValueError("A valid email is required")

    utm = payload.get("utm") or {}
    source = (payload.get("source") or "unknown")[:64]
    token = new_token()
    now = _now_iso()

    rows = await _query(db, "SELECT id, confirmed_at FROM lead_capture WHERE email = ?", email_lc)

    if not rows:
        await _run(
            db,
            """INSERT INTO lead_capture
               (email, source, utm_source, utm_medium, utm_campaign, utm_content,
                utm_term, referrer_url, magnet_requested, confirmation_token,
                sequence_step, created_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,0,?)""",
            email_lc,
            source,
            utm.get("source"),
            utm.get("medium"),
            utm.get("campaign"),
            utm.get("content"),
            utm.get("term"),
            payload.get("referrer_url"),
            1 if payload.get("magnet_requested", True) else 0,
            token,
            now,
        )
    elif rows[0]["confirmed_at"] is None:
        # Unconfirmed: refresh attribution along with the token.
        await _run(
            db,
            """UPDATE lead_capture
               SET confirmation_token=?, source=?, utm_source=?, utm_medium=?,
                   utm_campaign=?, utm_content=?, utm_term=?, referrer_url=?,
                   magnet_requested=?
               WHERE id=?""",
            token,
            source,
            utm.get("source"),
            utm.get("medium"),
            utm.get("campaign"),
            utm.get("content"),
            utm.get("term"),
            payload.get("referrer_url"),
            1 if payload.get("magnet_requested", True) else 0,
            rows[0]["id"],
        )
    else:
        # Already confirmed: rotate the token only (useful if they lost the
        # link) and leave their original attribution intact.
        await _run(
            db, "UPDATE lead_capture SET confirmation_token=? WHERE id=?", token, rows[0]["id"]
        )

    await send_confirmation(settings, email_lc, token)
    return {"status": "pending_confirmation"}


async def confirm(db, token: str) -> bool:
    """Activate a lead from its confirmation link. True when a row matched."""
    rows = await _query(
        db, "SELECT id, confirmed_at FROM lead_capture WHERE confirmation_token = ?", token
    )
    if not rows:
        return False
    if rows[0]["confirmed_at"] is None:
        await _run(
            db,
            "UPDATE lead_capture SET confirmed_at=?, unsubscribed_at=NULL WHERE id=?",
            _now_iso(),
            rows[0]["id"],
        )
    return True


async def unsubscribe(db, email: str) -> dict:
    """Revoke consent. Deliberately reports success even for an unknown email
    so the endpoint cannot be used to enumerate subscribers."""
    await _run(
        db,
        "UPDATE lead_capture SET unsubscribed_at=? WHERE email=? AND unsubscribed_at IS NULL",
        _now_iso(),
        (email or "").strip().lower(),
    )
    return {"status": "unsubscribed"}
