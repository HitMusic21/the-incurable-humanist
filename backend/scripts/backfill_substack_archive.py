"""One-shot backfill: import Denise's full Substack archive as published stories.

Supersedes the old scripts/import_substack.py, which read the RSS feed and so
could only ever see the 20 most recent posts (and filed them as drafts with
canonical_url pointing off-site).

Two phases, because the archive listing carries metadata but no bodies:

  1. page /api/v1/archive for every slug
  2. fetch /api/v1/posts/{slug} for each full body_html

Both phases run through app.services.substack_sync.upsert_entry, the same code
path the scheduled RSS sync uses, so backfill and sync cannot drift apart.
Re-running is safe: unchanged posts are skipped.

Usage:
    python backend/scripts/backfill_substack_archive.py --dry-run --limit 3
    python backend/scripts/backfill_substack_archive.py
"""

from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

import click
import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import settings  # noqa: E402
from app.core.database import async_session_maker  # noqa: E402
from app.services.substack_sync import (  # noqa: E402
    HTTP_HEADERS,
    coerce_datetime,
    fetch_api_body,
    fetch_archive_index,
    resolve_author,
    upsert_entry,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

# What the archive held when this script was written. Used as a tripwire, not a
# hard requirement — a silent short read is this script's likeliest failure.
EXPECTED_POST_COUNT = 71

# Substack is doing us a favour serving this; don't hammer it. 0.5s was too
# aggressive — a full run tripped 429 around post 43. fetch_api_body also
# retries with backoff, but pacing the happy path avoids provoking the limit
# in the first place.
REQUEST_DELAY_SECONDS = 1.5


async def _run(author_email: str, limit: int | None, dry_run: bool) -> None:
    async with httpx.AsyncClient(
        headers=HTTP_HEADERS, timeout=30.0, follow_redirects=True
    ) as client:
        index = await fetch_archive_index(client)
        found = len(index)
        click.echo(f"archive index: {found} posts")

        if found < EXPECTED_POST_COUNT:
            click.secho(
                f"WARNING: expected at least {EXPECTED_POST_COUNT} posts, got {found}. "
                "Suspect a short read — check the pager steps by len(page), not the "
                "requested limit.",
                fg="yellow",
            )
        elif found > EXPECTED_POST_COUNT:
            click.echo(f"note: archive has grown past {EXPECTED_POST_COUNT} (now {found}).")

        slugs = list(index)[: limit or len(index)]

        async with async_session_maker() as session:
            author = await resolve_author(session, author_email)

            stats = {"created": 0, "updated": 0, "skipped": 0, "failed": 0}
            for i, slug in enumerate(slugs, start=1):
                post = index[slug]
                try:
                    body = await fetch_api_body(client, slug)
                    if not body:
                        click.echo(f"  [{i}/{len(slugs)}] SKIP (no body): {slug}")
                        stats["failed"] += 1
                        continue

                    if dry_run:
                        click.echo(f"  [{i}/{len(slugs)}] would import: {post.get('title')!r}")
                        continue

                    outcome = await upsert_entry(
                        session,
                        author.id,
                        title=post.get("title") or "Untitled",
                        source_url=post.get("canonical_url") or "",
                        body_html=body,
                        published_at=coerce_datetime(post.get("post_date")),
                        cover_image_url=post.get("cover_image"),
                        source="api",
                    )
                    stats[outcome] += 1
                    click.echo(f"  [{i}/{len(slugs)}] {outcome}: {post.get('title')!r}")
                except Exception as exc:  # noqa: BLE001 - keep going, report at the end
                    stats["failed"] += 1
                    click.secho(f"  [{i}/{len(slugs)}] FAILED {slug}: {exc}", fg="red")

                await asyncio.sleep(REQUEST_DELAY_SECONDS)

            if dry_run:
                click.secho("\nDry run — nothing written.", fg="yellow")
                return

            await session.commit()

    click.secho(
        f"\nDone. created={stats['created']} updated={stats['updated']} "
        f"skipped={stats['skipped']} failed={stats['failed']}",
        fg="green" if not stats["failed"] else "yellow",
    )


@click.command()
@click.option("--author-email", default=None, help=f"defaults to {settings.AUTHOR_EMAIL}")
@click.option("--limit", type=int, default=None, help="only process the first N posts")
@click.option("--dry-run", is_flag=True, help="fetch and report, write nothing")
def main(author_email: str | None, limit: int | None, dry_run: bool) -> None:
    asyncio.run(_run(author_email or settings.AUTHOR_EMAIL, limit, dry_run))


if __name__ == "__main__":
    main()
