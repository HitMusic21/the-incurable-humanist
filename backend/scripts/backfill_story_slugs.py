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
import sys
from pathlib import Path

# Allow running as a standalone script: `python backend/scripts/backfill_story_slugs.py`
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.database import async_session_maker  # noqa: E402
from app.models.story import Story  # noqa: E402
from app.services.slugify import ensure_unique_slug, slugify  # noqa: E402
from sqlalchemy import select  # noqa: E402


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
