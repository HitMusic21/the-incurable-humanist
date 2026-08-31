"""Substack -> D1 `story` sync, ported from backend/app/services/substack_sync.py.

The SQLModel/asyncpg data layer is replaced by D1 prepared statements; the
*decision logic* is carried over unchanged, because each rule below was derived
from probing the live feed and is load-bearing:

  1. `/api/v1/archive` does not honour `limit` above ~23, so the pager steps by
     the number of items actually returned, never by the requested size.
     (Not used by the hourly sync — kept for the reconcile/backfill path.)
  2. Change detection hashes normalized TEXT, not markup, because RSS and the
     JSON API render identical prose with different image markup. Hashing
     markup would make every hourly run rewrite every row.
  3. RSS content never overwrites richer API content: on a genuine edit of an
     RSS-sourced row we re-fetch the JSON API body rather than storing the
     feed's poorer markup.
  4. `canonical_url` stays NULL so the on-site page is canonical. `source_url`
     is provenance *and* the idempotency key (UNIQUE).

Differences forced by the Workers runtime:
  - No `run_in_threadpool`; feedparser.parse() is called directly on the
    already-fetched bytes, which is CPU-only and does no I/O.
  - Datetimes are ISO-8601 TEXT (D1 is SQLite and has no datetime type).
  - No ORM session, so the concurrent-insert race is handled by catching the
    UNIQUE constraint error from D1 instead of SQLAlchemy's IntegrityError.
"""

from __future__ import annotations

import re
import time
import unicodedata
from datetime import datetime, timezone

import feedparser
import httpx

from html_sanitize import (
    content_hash,
    excerpt_from,
    read_time_minutes,
    sanitize_substack_html,
)

SUBSTACK_BASE = "https://theincurablehumanist.substack.com"
DEFAULT_FEED_URL = f"{SUBSTACK_BASE}/feed"
POST_URL = SUBSTACK_BASE + "/api/v1/posts/{slug}"

# Substack 403s urllib's default agent; pin one so we never depend on that.
USER_AGENT = "Mozilla/5.0 (compatible; TIH-sync/1.0; +https://theincurablehumanist.com)"
HTTP_HEADERS = {"User-Agent": USER_AGENT}

_SLUG_CLEAN_RE = re.compile(r"[^a-z0-9\s-]")
_SLUG_HYPHEN_RE = re.compile(r"[\s-]+")


def slugify(text: str) -> str:
    """Lowercase ASCII, hyphens for separators, never empty."""
    normalized = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    cleaned = _SLUG_CLEAN_RE.sub("", normalized.lower()).strip()
    return _SLUG_HYPHEN_RE.sub("-", cleaned).strip("-") or "essay"


def _now_iso() -> str:
    """UTC timestamp as strict ISO 8601 with a 'Z' offset.

    The separator and the offset are load-bearing, not cosmetic: these values
    are emitted verbatim as JSON-LD `datePublished`/`dateModified`, and
    Google's Rich Results validator rejects `2026-08-25 12:01:37` (space
    separator, no offset). Writing them correctly here means the API, RSS and
    sitemap all get a valid timestamp without per-consumer formatting.
    """
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


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


async def ensure_unique_slug(db, base: str, own_id: int | None = None) -> str:
    """Return `base`, or `base-2`, `base-3`, … until unique in `story.slug`."""
    candidate = base
    n = 2
    while True:
        if own_id is None:
            rows = await _query(db, "SELECT id FROM story WHERE slug = ?", candidate)
        else:
            rows = await _query(
                db, "SELECT id FROM story WHERE slug = ? AND id != ?", candidate, own_id
            )
        if not rows:
            return candidate
        candidate = f"{base}-{n}"
        n += 1


def _entry_body(entry) -> str:
    contents = entry.get("content") or []
    if contents and contents[0].get("value"):
        return contents[0]["value"]
    return entry.get("summary") or entry.get("description") or ""


def _entry_image(entry) -> str | None:
    for link in entry.get("links") or []:
        if link.get("rel") == "enclosure" and link.get("href"):
            return link["href"]
    return None


def _entry_published(entry) -> str | None:
    """Feed publish date as strict ISO 8601 UTC — see _now_iso on why."""
    parsed = entry.get("published_parsed") or entry.get("updated_parsed")
    if not parsed:
        return None
    # feedparser's *_parsed structs are already UTC.
    stamp = datetime.fromtimestamp(time.mktime(parsed), tz=timezone.utc)
    return stamp.isoformat(timespec="seconds").replace("+00:00", "Z")


async def fetch_api_body(client: httpx.AsyncClient, slug: str) -> str | None:
    """Full body_html for one post, or None when Substack 404s it.

    The Cloud Run version retried 429s with exponential backoff because a
    71-post backfill reliably trips the rate limit. The hourly sync only
    re-fetches posts that actually changed (typically zero, occasionally one),
    so a single attempt is right here — and a Worker cannot sleep for minutes.
    A failure falls back to the RSS body rather than aborting the run.
    """
    response = await client.get(POST_URL.format(slug=slug))
    if response.status_code in (404, 429):
        return None
    response.raise_for_status()
    return response.json().get("body_html") or None


async def upsert_entry(
    db,
    author_id: int,
    *,
    title: str,
    source_url: str,
    body_html: str,
    published_at: str | None,
    cover_image_url: str | None,
    source: str,
    client: httpx.AsyncClient | None = None,
) -> str:
    """Insert or update one story. Returns 'created' | 'updated' | 'skipped'."""
    clean = sanitize_substack_html(body_html)
    if not clean:
        return "skipped"
    digest = content_hash(clean)

    rows = await _query(
        db,
        "SELECT id, content_hash, status, title, cover_image_url FROM story WHERE source_url = ?",
        source_url,
    )

    if not rows:
        slug = await ensure_unique_slug(db, slugify(title or "essay"))
        now = _now_iso()
        try:
            await _run(
                db,
                """INSERT INTO story
                   (title, slug, canonical_url, source_url, content, content_hash,
                    content_source, excerpt, cover_image_url, status,
                    read_time_minutes, view_count, author_id,
                    created_at, updated_at, published_at)
                   VALUES (?, ?, NULL, ?, ?, ?, ?, ?, ?, 'published', ?, 0, ?, ?, ?, ?)""",
                (title or "Untitled")[:500],
                slug,
                # canonical_url stays NULL — we are canonical, never mirror source_url.
                source_url,
                clean,
                digest,
                source,
                (excerpt_from(clean)[:500] or None),
                cover_image_url,
                read_time_minutes(clean),
                author_id,
                now,
                now,
                published_at,
            )
        except Exception as exc:  # noqa: BLE001
            # A concurrent run may have inserted this same source_url (UNIQUE).
            # The winner's row is already correct, so treat it as a no-op.
            if "UNIQUE" in str(exc).upper():
                return "skipped"
            raise
        return "created"

    existing = rows[0]

    # Resurrection: the reconciler archives anything missing upstream, but posts
    # come back (unpublished then republished, or a transient archive gap).
    # Restore BEFORE the unchanged-hash early return — the hash matches in
    # exactly that case, which would otherwise leave the essay invisible forever.
    resurrected = False
    if existing["status"] == "archived":
        await _run(
            db, "UPDATE story SET status='published', updated_at=? WHERE id=?",
            _now_iso(), existing["id"],
        )
        resurrected = True

    if existing["content_hash"] == digest:
        # Text unchanged. Leave the row — and its richer markup — alone.
        return "updated" if resurrected else "skipped"

    # Genuine edit. Prefer the JSON API's markup: RSS omits <picture> and every
    # responsive srcset, so storing its body verbatim degrades the images.
    # Deliberately NOT gated on the stored content_source, so rss-sourced rows
    # converge on api quality instead of staying poor forever.
    if source == "rss" and client is not None:
        slug_part = source_url.rstrip("/").rsplit("/", 1)[-1]
        try:
            richer = await fetch_api_body(client, slug_part)
        except Exception:  # noqa: BLE001 - fall back to the RSS body
            richer = None
        if richer:
            candidate = sanitize_substack_html(richer)
            if candidate:
                clean = candidate
                digest = content_hash(clean)
                source = "api"

    # Slug is deliberately never re-minted: the URL is already indexed and shared.
    await _run(
        db,
        """UPDATE story SET title=?, content=?, content_hash=?, content_source=?,
               excerpt=?, cover_image_url=COALESCE(?, cover_image_url),
               read_time_minutes=?, updated_at=?
           WHERE id=?""",
        (title or existing["title"])[:500],
        clean,
        digest,
        source,
        (excerpt_from(clean)[:500] or None),
        cover_image_url,
        read_time_minutes(clean),
        _now_iso(),
        existing["id"],
    )
    return "updated"


async def sync_from_feed(db, author_id: int, feed_url: str = DEFAULT_FEED_URL) -> dict:
    """Sync the ~20 posts Substack exposes over RSS. Safe to run hourly."""
    created = updated = skipped = 0
    errors: list[str] = []

    async with httpx.AsyncClient(headers=HTTP_HEADERS, timeout=30.0, follow_redirects=True) as client:
        response = await client.get(feed_url)
        # Substack 429s back-to-back feed reads. On the hourly schedule this
        # never fires, but a manual run right after a scheduled one does hit it.
        # Treat it as "nothing to do this tick" rather than an error: the run is
        # idempotent, so the next tick picks up whatever changed.
        if response.status_code == 429:
            return {
                "created": 0, "updated": 0, "skipped": 0,
                "errors": ["429 from Substack feed — backing off until next run"],
            }
        response.raise_for_status()
        parsed = feedparser.parse(response.text)

        for entry in parsed.entries:
            link = entry.get("link")
            if not link:
                continue
            try:
                body = _entry_body(entry)
                if not body:
                    errors.append(f"{link}: empty body")
                    continue
                outcome = await upsert_entry(
                    db,
                    author_id,
                    title=entry.get("title", "Untitled"),
                    source_url=link,
                    body_html=body,
                    published_at=_entry_published(entry),
                    cover_image_url=_entry_image(entry),
                    source="rss",
                    client=client,
                )
                if outcome == "created":
                    created += 1
                elif outcome == "updated":
                    updated += 1
                else:
                    skipped += 1
            except Exception as exc:  # noqa: BLE001 - one bad post must not abort the batch
                errors.append(f"{link}: {exc}")

    return {"created": created, "updated": updated, "skipped": skipped, "errors": errors}
