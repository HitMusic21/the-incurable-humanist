"""
Backfill story.slug for any legacy rows (post-migration 0002, pre-migration 0003).

Runs the same slug-generation logic as the API's auto-slug: slugify(title)
with a numeric suffix on collision. Safe to re-run — skips rows that already
have a slug.

Usage:
    python backend/scripts/backfill_story_slugs.py
"""

from __future__ import annotations

import asyncio
import re
import sys
import unicodedata
from pathlib import Path

# Allow running as a standalone script: `python backend/scripts/backfill_story_slugs.py`
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.database import async_session_maker  # noqa: E402
from app.models.story import Story  # noqa: E402
from sqlalchemy import select  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: E402

_SLUG_CLEAN_RE = re.compile(r"[^a-z0-9\s-]")
_SLUG_HYPHEN_RE = re.compile(r"[\s-]+")


def slugify(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    cleaned = _SLUG_CLEAN_RE.sub("", normalized.lower()).strip()
    hyphenated = _SLUG_HYPHEN_RE.sub("-", cleaned).strip("-")
    return hyphenated or "essay"


async def ensure_unique_slug(session: AsyncSession, base: str, own_id: int | None) -> str:
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


async def main() -> None:
    async with async_session_maker() as session:
        rows = (
            await session.execute(select(Story).where(Story.slug.is_(None)))
        ).scalars().all()
        if not rows:
            print("No stories missing a slug.")
            return

        for row in rows:
            base = slugify(row.title)
            row.slug = await ensure_unique_slug(session, base, own_id=row.id)
            print(f"story #{row.id}: {row.title!r} → slug={row.slug!r}")
        await session.commit()
        print(f"Backfilled {len(rows)} rows.")


if __name__ == "__main__":
    asyncio.run(main())
