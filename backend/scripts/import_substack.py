"""
One-shot import: pull Denise's Substack RSS and hydrate `story` rows as drafts.

Idempotent — `INSERT ... ON CONFLICT (canonical_url) DO NOTHING`-equivalent
via a per-entry existence check. Existing stories are left alone (the admin
can edit or re-publish on-site to clear canonical_url).

Usage:
    python backend/scripts/import_substack.py
    python backend/scripts/import_substack.py --feed https://…/feed
    python backend/scripts/import_substack.py --author-email denise@theincurablehumanist.com
"""

from __future__ import annotations

import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path

import click
import feedparser
from dateutil import parser as date_parser

# Allow running as a standalone script.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.core.database import async_session_maker  # noqa: E402
from app.models.story import Story, StoryStatus  # noqa: E402
from app.models.user import User  # noqa: E402
from app.services.slugify import ensure_unique_slug, slugify  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

DEFAULT_FEED = "https://theincurablehumanist.substack.com/feed"


async def _resolve_author(session: AsyncSession, email: str) -> User:
    """Import needs an author_id to satisfy the FK. Use the AUTHOR_EMAIL account."""
    row = (
        await session.execute(select(User).where(User.email == email.lower()))
    ).scalar_one_or_none()
    if row is None:
        raise click.ClickException(
            f"Author {email!r} not found. Register it first via POST /auth/register, "
            "then re-run the import."
        )
    if not row.is_author:
        raise click.ClickException(
            f"User {email!r} exists but is_author is False. Fix that first (edit AUTHOR_EMAIL "
            "in settings or promote the user)."
        )
    return row


def _parse_published(entry) -> datetime | None:
    published = entry.get("published") or entry.get("updated")
    if not published:
        return None
    try:
        return date_parser.parse(published)
    except (ValueError, TypeError):
        return None


async def _import_one(session: AsyncSession, author_id: int, entry) -> str:
    canonical = entry.get("link", "").strip()
    title = entry.get("title", "").strip() or "Untitled"
    if not canonical:
        return f"SKIP (no link): {title!r}"

    existing = (
        await session.execute(select(Story).where(Story.canonical_url == canonical))
    ).scalar_one_or_none()
    if existing is not None:
        return f"EXISTS #{existing.id}: {title!r}"

    base_slug = slugify(title)
    slug = await ensure_unique_slug(session, base_slug)

    body = entry.get("content", [{}])[0].get("value") if entry.get("content") else None
    if not body:
        body = entry.get("summary") or entry.get("description") or ""

    story = Story(
        title=title,
        slug=slug,
        content=body,
        excerpt=(entry.get("summary") or "")[:500] or None,
        canonical_url=canonical,
        status=StoryStatus.DRAFT,
        author_id=author_id,
        published_at=_parse_published(entry),
    )
    session.add(story)
    return f"IMPORTED slug={slug!r}: {title!r}"


async def _run(feed_url: str, author_email: str) -> None:
    parsed = feedparser.parse(feed_url)
    if parsed.bozo:
        raise click.ClickException(f"Feed parse error: {parsed.bozo_exception!r}")
    entries = getattr(parsed, "entries", [])
    if not entries:
        logger.warning("Feed returned no entries — nothing to import.")
        return

    async with async_session_maker() as session:
        author = await _resolve_author(session, author_email)
        for entry in entries:
            msg = await _import_one(session, author.id, entry)
            click.echo(msg)
        await session.commit()

    click.secho(f"\nDone. Processed {len(entries)} entries.", fg="green")


@click.command()
@click.option("--feed", "feed_url", default=DEFAULT_FEED, show_default=True, help="RSS feed URL")
@click.option(
    "--author-email",
    "author_email",
    default=None,
    help=f"Author email (defaults to settings.AUTHOR_EMAIL={settings.AUTHOR_EMAIL})",
)
def main(feed_url: str, author_email: str | None) -> None:
    email = author_email or settings.AUTHOR_EMAIL
    asyncio.run(_run(feed_url, email))


if __name__ == "__main__":
    main()
