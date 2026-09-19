"""The hourly sync must not issue one D1 query per feed entry.

upsert_entry originally ran its own `SELECT ... WHERE source_url = ?` for every
entry, so a run made 20 sequential round-trips before doing useful work. With a
417KB feed to parse and 20 bodies to sanitize, that pushed the scheduled
invocation past the 2,000ms CPU limit: Cloudflare killed it with
`exceededCpu` (cpu=2010ms, wall=3786ms) every hour once the self.env fix made
the handler actually reach this code.

These tests pin the batching with a fake D1 that counts queries, because the
regression is invisible in behaviour — a per-entry lookup returns exactly the
same answer, just slowly enough to be killed.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(_SRC))

import substack_sync as ss  # noqa: E402


class _FakeStmt:
    def __init__(self, db, sql):
        self.db, self.sql, self.params = db, sql, ()

    def bind(self, *params):
        self.params = params
        return self

    async def all(self):
        self.db.queries.append(self.sql)

        class _Result:
            pass

        result = _Result()
        if "WHERE source_url" in self.sql:
            result.results = [r for r in self.db.rows if r["source_url"] == self.params[0]]
        elif "WHERE slug" in self.sql:
            result.results = []
        else:
            result.results = list(self.db.rows)
        return result

    async def run(self):
        self.db.queries.append("WRITE " + self.sql.split()[0])


class _FakeDB:
    """Minimal D1 stand-in that records every statement it is asked to run."""

    def __init__(self, rows):
        self.rows = rows
        self.queries: list[str] = []

    def prepare(self, sql):
        return _FakeStmt(self, sql)

    @property
    def source_url_lookups(self) -> int:
        return sum("WHERE source_url" in q for q in self.queries)


def _row(url="u1", slug="a", body="<p>hello world</p>"):
    return {
        "id": 1,
        "slug": slug,
        "source_url": url,
        "content_hash": ss.content_hash(ss.sanitize_substack_html(body)),
        "status": "published",
        "title": "A",
        "cover_image_url": None,
    }


@pytest.mark.asyncio
async def test_load_existing_uses_a_single_query():
    db = _FakeDB([_row(), _row(url="u2", slug="b")])
    cache = await ss.load_existing(db)
    assert len(db.queries) == 1, db.queries
    assert set(cache) == {"u1", "u2"}


@pytest.mark.asyncio
async def test_unchanged_entry_issues_no_query_at_all():
    """The common case: 20 entries, none edited. This must cost zero lookups."""
    db = _FakeDB([_row()])
    cache = await ss.load_existing(db)
    db.queries.clear()

    outcome = await ss.upsert_entry(
        db, 1, title="A", source_url="u1", body_html="<p>hello world</p>",
        published_at=None, cover_image_url=None, source="rss",
        existing=cache.get("u1"), existing_loaded=True,
    )
    assert outcome == "skipped"
    assert db.queries == [], f"expected no queries, got {db.queries}"


@pytest.mark.asyncio
async def test_absent_url_is_treated_as_new_without_a_lookup():
    """existing_loaded=True means None is authoritative, not 'not checked'.

    Without that distinction a cache miss would silently fall back to a
    per-entry query and undo the batching.
    """
    db = _FakeDB([_row()])
    cache = await ss.load_existing(db)
    db.queries.clear()

    outcome = await ss.upsert_entry(
        db, 1, title="New", source_url="u2", body_html="<p>brand new essay text</p>",
        published_at=None, cover_image_url=None, source="rss",
        existing=cache.get("u2"), existing_loaded=True,
    )
    assert outcome == "created"
    assert db.source_url_lookups == 0, db.queries


@pytest.mark.asyncio
async def test_callers_that_do_not_prefetch_still_work():
    """backfill/reconcile call upsert_entry without a cache; keep that path."""
    db = _FakeDB([_row()])
    outcome = await ss.upsert_entry(
        db, 1, title="A", source_url="u1", body_html="<p>hello world</p>",
        published_at=None, cover_image_url=None, source="rss",
    )
    assert outcome == "skipped"
    assert db.source_url_lookups == 1, db.queries


def test_sync_loop_prefetches_once_outside_the_entry_loop():
    """Structural guard: load_existing must not drift back inside the loop."""
    source = (_SRC / "substack_sync.py").read_text(encoding="utf-8")
    prefetch = source.index("existing_by_url = await load_existing(db)")
    loop = source.index("for entry in parsed.entries:")
    assert prefetch < loop, "prefetch must happen before the per-entry loop"


def test_the_sync_loop_actually_passes_the_prefetched_row():
    """The prefetch is useless unless the call site uses it.

    Checked inside the sync loop's own upsert_entry call specifically — an
    earlier version of this test asserted `existing_loaded=True` appeared
    anywhere in the file, which stayed true (it is in the signature's
    docstring) even after the call site stopped passing it.
    """
    source = (_SRC / "substack_sync.py").read_text(encoding="utf-8")
    loop = source.index("for entry in parsed.entries:")
    call_start = source.index("outcome = await upsert_entry(", loop)
    # Slice to the call's own closing paren — the one indented back to the
    # `await` level. Searching for the next ")" instead lands inside
    # entry.get(...), truncating the very arguments under test.
    call_end = source.index("\n                )", call_start)
    call = source[call_start:call_end]
    assert "existing=existing_by_url.get(link)" in call, call
    assert "existing_loaded=True" in call, call
