"""
SendGrid Event Webhook signature verification.

SendGrid signs each webhook batch with ECDSA P-256 over the concatenation
`timestamp + raw_body`. The public key comes from the SendGrid portal
(Settings → Mail Settings → Event Webhook → Signed Event Webhook Requests)
and is stored as `SENDGRID_WEBHOOK_PUBLIC_KEY` (PEM, base64-encoded body only
between the BEGIN/END markers is what SendGrid displays — we accept either
form).

Reference:
https://docs.sendgrid.com/for-developers/tracking-events/getting-started-event-webhook-security-features
"""

from __future__ import annotations

import base64
import logging

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec

from app.core.config import settings

logger = logging.getLogger(__name__)

SIGNATURE_HEADER = "X-Twilio-Email-Event-Webhook-Signature"
TIMESTAMP_HEADER = "X-Twilio-Email-Event-Webhook-Timestamp"


def _load_public_key():
    raw = (settings.SENDGRID_WEBHOOK_PUBLIC_KEY or "").strip()
    if not raw:
        return None
    # Accept either raw base64 (as shown in the SendGrid UI) or full PEM.
    if "BEGIN PUBLIC KEY" not in raw:
        raw = f"-----BEGIN PUBLIC KEY-----\n{raw}\n-----END PUBLIC KEY-----"
    try:
        return serialization.load_pem_public_key(raw.encode("utf-8"))
    except Exception:
        logger.exception("Failed to parse SENDGRID_WEBHOOK_PUBLIC_KEY")
        return None


def verify(signature_b64: str | None, timestamp: str | None, raw_body: bytes) -> bool:
    """Return True if the request's signature verifies against the configured key.
    Returns False for any failure (missing header, missing key, bad signature)."""
    if not signature_b64 or not timestamp:
        return False
    public_key = _load_public_key()
    if public_key is None:
        return False
    if not isinstance(public_key, ec.EllipticCurvePublicKey):
        logger.error("SENDGRID_WEBHOOK_PUBLIC_KEY is not an ECDSA key")
        return False

    try:
        signature = base64.b64decode(signature_b64)
    except Exception:
        return False

    payload = timestamp.encode("utf-8") + raw_body
    # SendGrid hashes with SHA-256 and signs the digest with ECDSA P-256.
    # `cryptography` handles the digest for us via ECDSA(hashes.SHA256()).
    try:
        public_key.verify(signature, payload, ec.ECDSA(hashes.SHA256()))
        return True
    except InvalidSignature:
        return False
    except Exception:
        logger.exception("SendGrid signature verification raised unexpectedly")
        return False
