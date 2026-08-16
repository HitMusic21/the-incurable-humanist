"""Substack -> `story` sync.

Single source of truth for turning a Substack post into a `story` row. The
scheduled RSS endpoint, the one-shot archive backfill and the deletion
reconciler all funnel through `upsert_entry`, so they cannot drift apart.

Idempotency key is `story.source_url` (the exact Substack permalink, UNIQUE).

Four behaviours here are load-bearing and were each derived from probing the
live feed — see the notes on the functions that implement them:

  1. `/api/v1/archive` does not honour `limit` above ~23, so the pager steps by
     the number of items actually returned, never by the requested size.
  2. Change detection hashes normalized TEXT, not markup, because RSS and the
     JSON API render identical prose with different image markup.
  3. RSS content never overwrites richer API content (`content_source`).
  4. Deletion reconciliation archives rather than deletes, and refuses to act
     on an implausibly small corpus.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal

import feedparser
import httpx
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.models.story import Story, StoryStatus
from app.models.user import User
from app.services.html_sanitize import (
    content_hash,
    excerpt_from,
    read_time_minutes,
    sanitize_substack_html,
)
from app.services.slugify import ensure_unique_slug, slugify

logger = logging.getLogger(__name__)

SUBSTACK_BASE = "https://theincurablehumanist.substack.com"
DEFAULT_FEED_URL = f"{SUBSTACK_BASE}/feed"
ARCHIVE_URL = f"{SUBSTACK_BASE}/api/v1/archive"
POST_URL = f"{SUBSTACK_BASE}/api/v1/posts/{{slug}}"

# Substack 403s urllib's default agent; httpx works either way, but pin one so
# we never depend on that.
USER_AGENT = "Mozilla/5.0 (compatible; TIH-sync/1.0; +https://theincurablehumanist.com)"
HTTP_HEADERS = {"User-Agent": USER_AGENT}

# The archive endpoint caps page size around 23 regardless of what we ask for.
# Request a size comfortably below that so every page is served whole.
ARCHIVE_PAGE_SIZE = 12

# Refuse to archive more than this share of the corpus in one reconcile run.
# A larger delta means a Substack outage or a pagination regression, not real
# deletions.
MAX_ARCHIVE_RATIO = 0.10

# Substack 429s a sustained backfill. Observed: ~43 posts fetched back-to-back
# before it starts refusing. Back off and retry rather than failing the run.
RATE_LIMIT_MAX_ATTEMPTS = 5
RATE_LIMIT_BASE_DELAY = 5.0

ContentSource = Literal["api", "rss"]


@dataclass
class SyncResult:
    created: int = 0
    updated: int = 0
    skipped: int = 0
    errors: list[str] = field(default_factory=list)

    def record(self, outcome: str) -> None:
        setattr(self, outcome, getattr(self, outcome) + 1)


async def resolve_author(session: AsyncSession, email: str) -> User:
    """Resolve the author row that imported stories hang off.

    Fails loudly rather than auto-creating or defaulting to id 1 — an import
    silently attributed to the wrong user is worse than one that refuses to run.
    """
    author = (
        await session.execute(select(User).where(User.email == email.lower()))
    ).scalar_one_or_none()
    if author is None:
        raise RuntimeError(
            f"Author {email!r} not found. Register it via POST /auth/register, then re-run."
        )
    if not author.is_author:
        raise RuntimeError(
            f"User {email!r} exists but is_author is False. Promote the user first."
        )
    return author


def coerce_datetime(value: Any) -> datetime | None:
    """Substack sends ISO-8601 with a trailing Z; the column is naive UTC."""
    if not value:
        return None
    if isinstance(value, datetime):
        return value.replace(tzinfo=None)
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    return parsed.replace(tzinfo=None)


async def upsert_entry(
    session: AsyncSession,
    author_id: int,
    *,
    title: str,
    source_url: str,
    body_html: str,
    published_at: datetime | None,
    cover_image_url: str | None,
    source: ContentSource,
    refetch_api: Callable[[str], Awaitable[str | None]] | None = None,
) -> str:
    """Insert, update or skip one Substack post. Returns the outcome name.

    Change detection compares a hash of the *text*, so a post that is unchanged
    upstream is skipped no matter which endpoint it arrived from.

    When a genuinely edited post arrives over RSS but the stored row came from
    the JSON API, `refetch_api` is used to pull the richer body: RSS markup has
    no <picture> and no responsive srcset, so taking it verbatim would quietly
    downgrade every image on the page.
    """
    source_url = (source_url or "").strip()
    if not source_url:
        raise ValueError("source_url is required — it is the idempotency key")

    clean = sanitize_substack_html(body_html)
    if not clean:
        raise ValueError(f"empty body after sanitize for {source_url!r}")
    digest = content_hash(clean)

    existing = (
        await session.execute(select(Story).where(Story.source_url == source_url))
    ).scalar_one_or_none()

    if existing is None:
        story = Story(
            title=(title or "Untitled")[:500],
            slug=await ensure_unique_slug(session, slugify(title or "essay")),
            source_url=source_url,
            # We are canonical. Never mirror source_url here.
            canonical_url=None,
            content=clean,
            content_hash=digest,
            content_source=source,
            excerpt=excerpt_from(clean)[:500] or None,
            cover_image_url=cover_image_url,
            status=StoryStatus.PUBLISHED,
            read_time_minutes=read_time_minutes(clean),
            author_id=author_id,
            published_at=published_at,
        )
        session.add(story)
        # Flush now rather than at the batch commit. Two reasons:
        #   1. A concurrent sync may have inserted this same source_url between
        #      the SELECT above and here. Flushing surfaces that IntegrityError
        #      on THIS entry, where the caller can skip it, instead of at the
        #      final commit where it would fail the whole batch.
        #   2. Without a flush, the NEXT entry's ensure_unique_slug() query
        #      triggers an autoflush that raises the error out of unrelated
        #      code and leaves the session unusable for the rest of the run.
        try:
            await session.flush()
        except IntegrityError:
            # Lost the race. The winner's row is already correct — treat this
            # as a no-op rather than an error, but roll back to a clean state
            # first or every later entry inherits the poisoned transaction.
            await session.rollback()
            logger.info("concurrent insert for %s — skipping", source_url)
            return "skipped"
        return "created"

    # Resurrection: the reconciler archives anything missing from the upstream
    # corpus, but Substack posts come back (unpublished then republished, or a
    # transient gap in the archive listing). Seeing it in a sync means it is
    # live again, so restore it BEFORE the unchanged-text early return — the
    # hash matches in exactly that case, which would otherwise leave the essay
    # archived and invisible forever.
    resurrected = False
    if existing.status == StoryStatus.ARCHIVED:
        existing.status = StoryStatus.PUBLISHED
        existing.updated_at = datetime.utcnow()
        resurrected = True
        logger.info("un-archived %s — it is live upstream again", source_url)

    if existing.content_hash == digest:
        # Text is unchanged. Leave the row — and its richer markup — alone.
        return "updated" if resurrected else "skipped"

    # Genuine edit. Prefer API markup when the stored row already has it.
    if source == "rss" and existing.content_source == "api" and refetch_api is not None:
        slug = source_url.rstrip("/").rsplit("/", 1)[-1]
        try:
            richer = await refetch_api(slug)
        except Exception as exc:  # noqa: BLE001 - fall back to the RSS body
            logger.warning("refetch_api failed for %s: %s", slug, exc)
            richer = None
        if richer:
            candidate = sanitize_substack_html(richer)
            if candidate:
                clean = candidate
                digest = content_hash(clean)
                source = "api"

    existing.title = (title or existing.title)[:500]
    existing.content = clean
    existing.content_hash = digest
    existing.content_source = source
    existing.excerpt = excerpt_from(clean)[:500] or None
    if cover_image_url:
        existing.cover_image_url = cover_image_url
    existing.read_time_minutes = read_time_minutes(clean)
    existing.updated_at = datetime.utcnow()
    # Slug is deliberately never re-minted: the URL is already indexed and shared.
    return "updated"


def _entry_body(entry: Any) -> str:
    contents = entry.get("content") or []
    if contents and contents[0].get("value"):
        return contents[0]["value"]
    return entry.get("summary") or entry.get("description") or ""


def _entry_image(entry: Any) -> str | None:
    for link in entry.get("links") or []:
        if link.get("rel") == "enclosure" and link.get("href"):
            return link["href"]
    return None


def _entry_published(entry: Any) -> datetime | None:
    parsed = entry.get("published_parsed") or entry.get("updated_parsed")
    if not parsed:
        return None
    import time

    return datetime.fromtimestamp(time.mktime(parsed))


async def fetch_api_body(client: httpx.AsyncClient, slug: str) -> str | None:
    """Full body_html for one post, or None when Substack 404s it.

    Substack rate-limits sustained per-post fetching — a full 71-post backfill
    reliably trips 429 partway through — so retry with exponential backoff and
    honour Retry-After when it is sent. Callers stay idempotent regardless, but
    without this a single backfill run cannot finish.
    """
    delay = RATE_LIMIT_BASE_DELAY
    last_error: Exception | None = None

    for attempt in range(1, RATE_LIMIT_MAX_ATTEMPTS + 1):
        response = await client.get(POST_URL.format(slug=slug))
        if response.status_code == 404:
            return None
        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            wait = float(retry_after) if (retry_after or "").isdigit() else delay
            logger.info(
                "429 for %s (attempt %s/%s) — waiting %.1fs",
                slug, attempt, RATE_LIMIT_MAX_ATTEMPTS, wait,
            )
            await asyncio.sleep(wait)
            delay *= 2
            last_error = httpx.HTTPStatusError(
                "429 Too Many Requests", request=response.request, response=response
            )
            continue
        response.raise_for_status()
        return response.json().get("body_html") or None

    raise last_error or RuntimeError(f"exhausted retries fetching {slug!r}")


async def fetch_archive_index(client: httpx.AsyncClient) -> dict[str, dict]:
    """Every post Substack still publishes, keyed by slug.

    `limit` is not honoured above ~23, so advancing the offset by the requested
    page size skips records and then hits an empty page that looks like a clean
    finish. Advance by what actually came back instead.
    """
    posts: dict[str, dict] = {}
    offset = 0
    while True:
        response = await client.get(
            ARCHIVE_URL,
            params={"sort": "new", "offset": offset, "limit": ARCHIVE_PAGE_SIZE},
        )
        response.raise_for_status()
        page = response.json()
        if not page:
            break
        for post in page:
            if post.get("slug"):
                posts[post["slug"]] = post
        offset += len(page)
    return posts


async def sync_from_feed(
    session: AsyncSession,
    *,
    author_id: int,
    feed_url: str = DEFAULT_FEED_URL,
) -> SyncResult:
    """Sync the ~20 posts Substack exposes over RSS. Safe to run on a schedule."""
    result = SyncResult()

    async with httpx.AsyncClient(
        headers=HTTP_HEADERS, timeout=30.0, follow_redirects=True
    ) as client:
        response = await client.get(feed_url)
        response.raise_for_status()
        raw_feed = response.text

        # feedparser is blocking; keep it off the event loop.
        parsed = await run_in_threadpool(feedparser.parse, raw_feed)
        if getattr(parsed, "bozo", False) and not getattr(parsed, "entries", []):
            raise RuntimeError(f"Feed parse error: {parsed.get('bozo_exception')!r}")

        async def refetch(slug: str) -> str | None:
            return await fetch_api_body(client, slug)

        for entry in getattr(parsed, "entries", []):
            link = (entry.get("link") or "").strip()
            try:
                body = _entry_body(entry)
                if not body:
                    result.errors.append(f"{link}: empty body")
                    continue
                outcome = await upsert_entry(
                    session,
                    author_id,
                    title=entry.get("title", "Untitled"),
                    source_url=link,
                    body_html=body,
                    published_at=_entry_published(entry),
                    cover_image_url=_entry_image(entry),
                    source="rss",
                    refetch_api=refetch,
                )
                result.record(outcome)
            except Exception as exc:  # noqa: BLE001 - one bad post must not abort the batch
                logger.warning("sync_from_feed: %s failed: %s", link, exc)
                result.errors.append(f"{link}: {exc}")
                # A failed flush leaves the session in a rolled-back state where
                # every later query raises. Reset so the remaining entries still
                # get their turn — "one bad post must not abort the batch" is
                # only true if we actually clear the error.
                # Already unusable if this fails; nothing left to salvage.
                with contextlib.suppress(Exception):
                    await session.rollback()

    await session.commit()
    logger.info(
        "sync_from_feed: created=%s updated=%s skipped=%s errors=%s",
        result.created, result.updated, result.skipped, len(result.errors),
    )
    return result


async def reconcile_deletions(
    session: AsyncSession,
    *,
    live_source_urls: set[str],
    dry_run: bool = True,
) -> list[Story]:
    """Archive synced stories that Substack no longer publishes.

    RSS only carries what currently exists, so a deleted post simply stops
    appearing — its on-site copy would otherwise stay live and indexed forever.
    Authority therefore has to be the full archive corpus, never the 20-item
    feed, which would archive the entire back catalogue on its first run.

    Rows are ARCHIVED, never deleted: view counts survive and the change is
    reversible. `GET /stories` and `/stories/{slug}` already exclude archived
    rows, so the sitemap and reader page need no changes.
    """
    if not live_source_urls:
        raise RuntimeError(
            "Refusing to reconcile against an empty corpus — treat as an upstream outage."
        )

    synced = (
        (
            await session.execute(
                select(Story).where(
                    Story.source_url.is_not(None),
                    Story.status != StoryStatus.ARCHIVED,
                )
            )
        )
        .scalars()
        .all()
    )
    missing = [s for s in synced if s.source_url not in live_source_urls]
    if not missing:
        return []

    if synced and len(missing) / len(synced) > MAX_ARCHIVE_RATIO:
        raise RuntimeError(
            f"Refusing to archive {len(missing)}/{len(synced)} stories "
            f"(>{MAX_ARCHIVE_RATIO:.0%}). Likely an upstream outage or a pagination bug."
        )

    if not dry_run:
        for story in missing:
            story.status = StoryStatus.ARCHIVED
            story.updated_at = datetime.utcnow()
        await session.commit()

    logger.info(
        "reconcile_deletions: %s story/ies %s",
        len(missing), "would be archived (dry run)" if dry_run else "archived",
    )
    return missing
