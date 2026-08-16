"""Slug generation utility, shared between the API auto-slug flow and the
backfill CLI. Kept small and dependency-free."""

from __future__ import annotations

import re
import unicodedata

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.story import Story

_SLUG_CLEAN_RE = re.compile(r"[^a-z0-9\s-]")
_SLUG_HYPHEN_RE = re.compile(r"[\s-]+")


def slugify(text: str) -> str:
    """Lowercase ASCII, hyphens for separators, never empty."""
    normalized = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    cleaned = _SLUG_CLEAN_RE.sub("", normalized.lower()).strip()
    hyphenated = _SLUG_HYPHEN_RE.sub("-", cleaned).strip("-")
    return hyphenated or "essay"


async def ensure_unique_slug(
    session: AsyncSession, base: str, own_id: int | None = None
) -> str:
    """Return `base`, or `base-2`, `base-3`, … until it's unique in `story.slug`.
    Pass `own_id` when updating an existing row so it doesn't collide with itself.
    """
    candidate = base
    n = 2
    while True:
        stmt = select(Story).where(Story.slug == candidate)
        if own_id is not None:
            stmt = stmt.where(Story.id != own_id)
        existing = (await session.execute(stmt)).scalar_one_or_none()
        if existing is None:
            return candidate
        candidate = f"{base}-{n}"
        n += 1
