"""Archive stories whose Substack source no longer exists.

RSS only carries what currently exists, so a post deleted or unpublished
upstream simply stops appearing in the feed — its on-site copy would otherwise
stay live and indexed indefinitely. This job closes that gap.

Authority is the full /api/v1/archive corpus, never the 20-item RSS window: a
feed-based reconcile would archive the entire back catalogue on its first run.

Rows are ARCHIVED, never deleted, so view counts survive and the change is
reversible. Archived rows already drop out of GET /stories and 404 on
/stories/{slug}, so the sitemap and reader page need no changes.

Dry run is the default; --apply is required to write. Run weekly, not hourly:
deletion is rare and the frequent path should not hold this authority.

Usage:
    python backend/scripts/reconcile_substack.py
    python backend/scripts/reconcile_substack.py --apply
"""

from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

import click
import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.database import async_session_maker  # noqa: E402
from app.services.substack_sync import (  # noqa: E402
    HTTP_HEADERS,
    fetch_archive_index,
    reconcile_deletions,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


async def _run(apply: bool) -> None:
    async with httpx.AsyncClient(
        headers=HTTP_HEADERS, timeout=30.0, follow_redirects=True
    ) as client:
        index = await fetch_archive_index(client)

    live_urls = {p.get("canonical_url") for p in index.values() if p.get("canonical_url")}
    click.echo(f"live Substack posts: {len(live_urls)}")

    async with async_session_maker() as session:
        try:
            missing = await reconcile_deletions(
                session, live_source_urls=live_urls, dry_run=not apply
            )
        except RuntimeError as exc:
            # Safety rail tripped — empty corpus or an implausible delta.
            click.secho(f"ABORTED: {exc}", fg="red")
            raise SystemExit(1) from exc

    if not missing:
        click.secho("Nothing to archive — on-site archive matches Substack.", fg="green")
        return

    for story in missing:
        click.echo(f"  {'archived' if apply else 'would archive'}: {story.slug} ({story.title!r})")

    if apply:
        click.secho(f"\nArchived {len(missing)} story/ies.", fg="green")
    else:
        click.secho(
            f"\nDry run — {len(missing)} would be archived. Re-run with --apply.",
            fg="yellow",
        )


@click.command()
@click.option("--apply", is_flag=True, help="actually archive (default is a dry run)")
def main(apply: bool) -> None:
    asyncio.run(_run(apply))


if __name__ == "__main__":
    main()
