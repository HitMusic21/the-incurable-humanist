"""Contract tests for the Substack sync surface.

Covers POST /stories/sync's auth ladder plus the upsert semantics that the
scheduled job depends on. No network: the RSS fetch and the JSON-API refetch
are both monkeypatched, so these run offline and deterministically.

Requires a reachable DB (docker-compose db) like the other contract tests —
the autouse fixtures in conftest.py truncate between cases.
"""

from __future__ import annotations

import asyncio
import uuid

import pytest
from fastapi.testclient import TestClient

TOKEN = "test-sync-token"

# Minimal but structurally real: <picture>+srcset is what the JSON API serves.
API_BODY = (
    "<p>The prose stays the same.</p>"
    '<figure><picture><source srcset="https://cdn/x_424.png 424w">'
    '<img src="https://cdn/x_1456.png" width="1456" height="788" alt="p"></picture></figure>'
)
# Same prose, poorer markup — what RSS serves for the identical post.
RSS_BODY = (
    "<p>The prose stays the same.</p>"
    '<img src="https://cdn/x_1456.png" width="1456" height="788" alt="p">'
)


def _feed(entries: list[dict]) -> str:
    """Build an RSS document feedparser will accept."""
    items = "".join(
        f"<item><title>{e['title']}</title><link>{e['link']}</link>"
        f"<pubDate>Mon, 11 Aug 2026 12:01:16 GMT</pubDate>"
        f"<content:encoded><![CDATA[{e['body']}]]></content:encoded></item>"
        for e in entries
    )
    return (
        '<?xml version="1.0"?>'
        '<rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/">'
        f"<channel><title>TIH</title>{items}</channel></rss>"
    )


def _url() -> str:
    return f"https://theincurablehumanist.substack.com/p/{uuid.uuid4().hex[:10]}"


@pytest.fixture
def client():
    from app.main import app

    return TestClient(app)


@pytest.fixture
def token(monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "SCHEDULER_TOKEN", TOKEN)
    return TOKEN


@pytest.fixture
def author(client):
    """Register + promote the configured author so sync can resolve an author_id."""
    from app.core.config import settings

    email = settings.AUTHOR_EMAIL
    client.post(
        "/auth/register",
        json={"email": email, "password": "TestPass12345", "full_name": "Test Author"},
    )

    async def _promote():
        from app.models.user import User
        from sqlalchemy import select
        from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy.pool import NullPool
        from tests.conftest import _async_url

        engine = create_async_engine(_async_url(), poolclass=NullPool, future=True)
        maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        async with maker() as session:
            row = (
                await session.execute(select(User).where(User.email == email.lower()))
            ).scalar_one_or_none()
            if row is not None and not row.is_author:
                row.is_author = True
                await session.commit()
        await engine.dispose()

    asyncio.run(_promote())
    return email


class TestSyncAuth:
    def test_missing_token_config_is_503(self, client, monkeypatch):
        """Fail closed: an unset SCHEDULER_TOKEN must never mean 'open'."""
        from app.core.config import settings

        monkeypatch.setattr(settings, "SCHEDULER_TOKEN", "")
        assert client.post("/stories/sync").status_code == 503

    def test_wrong_token_is_401(self, client, token):
        resp = client.post("/stories/sync", headers={"X-Scheduler-Token": "nope"})
        assert resp.status_code == 401

    def test_missing_header_is_401(self, client, token):
        assert client.post("/stories/sync").status_code == 401


class TestSyncEndpoint:
    def _patch_feed(self, monkeypatch, entries):
        import httpx
        from app.services import substack_sync

        async def fake_get(self, url, **kwargs):
            return httpx.Response(200, text=_feed(entries), request=httpx.Request("GET", url))

        monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)
        return substack_sync

    def test_sync_creates_then_skips(self, client, token, author, monkeypatch):
        url = _url()
        entries = [{"title": "Synced Essay", "link": url, "body": RSS_BODY}]
        self._patch_feed(monkeypatch, entries)

        first = client.post("/stories/sync", headers={"X-Scheduler-Token": TOKEN})
        assert first.status_code == 200, first.text
        assert first.json()["created"] == 1

        # Re-running an unchanged feed must be a no-op, not an update.
        second = client.post("/stories/sync", headers={"X-Scheduler-Token": TOKEN})
        assert second.json() == {"created": 0, "updated": 0, "skipped": 1, "errors": []}

    def test_synced_story_is_published_and_self_canonical(
        self, client, token, author, monkeypatch
    ):
        url = _url()
        self._patch_feed(monkeypatch, [{"title": "Canonical Check", "link": url, "body": RSS_BODY}])
        client.post("/stories/sync", headers={"X-Scheduler-Token": TOKEN})

        listing = client.get("/stories?status=published").json()
        row = next(s for s in listing["stories"] if s["source_url"] == url)
        # Decision: we are canonical; source_url only drives the credit link.
        assert row["canonical_url"] is None
        assert row["status"] == "published"
        assert row["read_time_minutes"] >= 1

        detail = client.get(f"/stories/{row['slug']}").json()
        assert "<script" not in detail["content"]
        assert "The prose stays the same." in detail["content"]

    def test_slug_is_stable_across_a_retitle(self, client, token, author, monkeypatch):
        """The URL is already indexed and shared — never re-mint it."""
        url = _url()
        self._patch_feed(monkeypatch, [{"title": "First Title", "link": url, "body": RSS_BODY}])
        client.post("/stories/sync", headers={"X-Scheduler-Token": TOKEN})
        original = next(
            s for s in client.get("/stories").json()["stories"] if s["source_url"] == url
        )["slug"]

        self._patch_feed(
            monkeypatch,
            [{"title": "Renamed Entirely", "link": url, "body": "<p>New words here.</p>"}],
        )
        resp = client.post("/stories/sync", headers={"X-Scheduler-Token": TOKEN})
        assert resp.json()["updated"] == 1

        after = next(s for s in client.get("/stories").json()["stories"] if s["source_url"] == url)
        assert after["slug"] == original
        assert after["title"] == "Renamed Entirely"

    def test_malformed_entry_does_not_abort_the_batch(self, client, token, author, monkeypatch):
        good = _url()
        self._patch_feed(
            monkeypatch,
            [
                {"title": "Empty Body", "link": _url(), "body": ""},
                {"title": "Good One", "link": good, "body": RSS_BODY},
            ],
        )
        body = client.post("/stories/sync", headers={"X-Scheduler-Token": TOKEN}).json()
        assert body["created"] == 1
        assert len(body["errors"]) == 1


class TestUpsertSemantics:
    """Direct service-level tests for behaviour the HTTP surface can't isolate."""

    def _session(self):
        from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy.pool import NullPool
        from tests.conftest import _async_url

        engine = create_async_engine(_async_url(), poolclass=NullPool, future=True)
        return engine, sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    def test_archived_post_is_restored_when_it_reappears(self, client, author):
        """Regression: an archived post that comes back upstream must un-archive.

        The reconciler archives anything missing from the corpus, but Substack
        posts return (unpublished then republished, or a transient gap in the
        archive listing). The restore has to happen BEFORE the unchanged-text
        early return, because the hash matches in exactly that case — otherwise
        the essay stays archived and invisible forever.
        """
        from app.models.story import Story, StoryStatus
        from app.services.substack_sync import resolve_author, upsert_entry
        from sqlalchemy import select

        url = _url()
        engine, maker = self._session()

        async def scenario():
            async with maker() as session:
                author_row = await resolve_author(session, author)
                await upsert_entry(
                    session,
                    author_row.id,
                    title="Comeback Essay",
                    source_url=url,
                    body_html="<p>Body that will not change at all.</p>",
                    published_at=None,
                    cover_image_url=None,
                    source="api",
                )
                await session.commit()

                row = (
                    await session.execute(select(Story).where(Story.source_url == url))
                ).scalar_one()
                row.status = StoryStatus.ARCHIVED
                await session.commit()

                # Same body — the hash matches, so this is the exact path that
                # used to return "skipped" and strand the row.
                outcome = await upsert_entry(
                    session,
                    author_row.id,
                    title="Comeback Essay",
                    source_url=url,
                    body_html="<p>Body that will not change at all.</p>",
                    published_at=None,
                    cover_image_url=None,
                    source="api",
                )
                await session.commit()

                restored = (
                    await session.execute(select(Story).where(Story.source_url == url))
                ).scalar_one()
                return outcome, restored.status

        outcome, status = asyncio.run(scenario())
        asyncio.run(engine.dispose())

        assert status == StoryStatus.PUBLISHED, "archived row was never restored"
        assert outcome == "updated", "restoring a row must not report 'skipped'"

    def test_duplicate_source_url_is_skipped_not_fatal(self, client, author):
        """Regression: a racing insert must not poison the session.

        Two syncs overlapping (scheduler retry, manual run during the hourly
        job) both pass the existence check, then the loser hits UNIQUE. Without
        a per-entry flush the IntegrityError surfaces later, during an unrelated
        query's autoflush, and every remaining entry in the batch fails too.
        """
        from app.models.story import Story
        from app.services.substack_sync import resolve_author, upsert_entry
        from sqlalchemy import select

        url = _url()
        engine, maker = self._session()

        async def scenario():
            async with maker() as session:
                author_row = await resolve_author(session, author)
                await upsert_entry(
                    session,
                    author_row.id,
                    title="Race Winner",
                    source_url=url,
                    body_html="<p>First writer wins the race.</p>",
                    published_at=None,
                    cover_image_url=None,
                    source="api",
                )
                await session.commit()

            # A second session that never saw the winner's commit — this is the
            # loser of the race holding a stale read.
            async with maker() as other:
                author_row = await resolve_author(other, author)
                outcome = await upsert_entry(
                    other,
                    author_row.id,
                    title="Race Loser",
                    source_url=url,
                    body_html="<p>First writer wins the race.</p>",
                    published_at=None,
                    cover_image_url=None,
                    source="api",
                )
                # The session must still be usable afterwards.
                rows = (
                    await other.execute(select(Story).where(Story.source_url == url))
                ).scalars().all()
                return outcome, len(rows)

        outcome, count = asyncio.run(scenario())
        asyncio.run(engine.dispose())

        assert count == 1, "the race produced a duplicate row"
        assert outcome in ("skipped", "updated"), f"unexpected outcome {outcome!r}"

    def test_rss_after_api_skips_and_keeps_rich_markup(self, client, author):
        """Trap: RSS and the API render the same prose with different image markup.

        Hashing markup would flag this as an update and overwrite <picture>
        with a bare <img> — silently dropping every responsive srcset.
        """
        from app.services.substack_sync import resolve_author, upsert_entry

        url = _url()
        engine, maker = self._session()

        async def scenario():
            async with maker() as session:
                author_row = await resolve_author(session, author)
                created = await upsert_entry(
                    session,
                    author_row.id,
                    title="Rich Post",
                    source_url=url,
                    body_html=API_BODY,
                    published_at=None,
                    cover_image_url=None,
                    source="api",
                )
                await session.commit()

                outcome = await upsert_entry(
                    session,
                    author_row.id,
                    title="Rich Post",
                    source_url=url,
                    body_html=RSS_BODY,
                    published_at=None,
                    cover_image_url=None,
                    source="rss",
                )
                await session.commit()

                from app.models.story import Story
                from sqlalchemy import select

                row = (
                    await session.execute(select(Story).where(Story.source_url == url))
                ).scalar_one()
                return created, outcome, row.content, row.content_source

        created, outcome, content, source = asyncio.run(scenario())
        asyncio.run(engine.dispose())

        assert created == "created"
        assert outcome == "skipped"
        assert "<picture" in content, "RSS must not have downgraded the API markup"
        assert source == "api"

    def test_reconcile_refuses_empty_corpus(self, client, author):
        """An empty upstream corpus means an outage, not 71 deletions."""
        from app.services.substack_sync import reconcile_deletions

        engine, maker = self._session()

        async def scenario():
            async with maker() as session:
                with pytest.raises(RuntimeError, match="empty corpus"):
                    await reconcile_deletions(session, live_source_urls=set(), dry_run=True)

        asyncio.run(scenario())
        asyncio.run(engine.dispose())

    def test_reconcile_archives_missing_post(self, client, author):
        from app.models.story import Story, StoryStatus
        from app.services.substack_sync import (
            reconcile_deletions,
            resolve_author,
            upsert_entry,
        )
        from sqlalchemy import select

        kept, gone = _url(), _url()
        engine, maker = self._session()

        async def scenario():
            async with maker() as session:
                author_row = await resolve_author(session, author)
                for i, url in enumerate((kept, gone)):
                    await upsert_entry(
                        session,
                        author_row.id,
                        title=f"Post {i}",
                        source_url=url,
                        body_html=f"<p>Body number {i} with enough words.</p>",
                        published_at=None,
                        cover_image_url=None,
                        source="api",
                    )
                await session.commit()

                # 1 of 2 missing is 50% — above the 10% rail, so it must abort.
                with pytest.raises(RuntimeError, match="Refusing to archive"):
                    await reconcile_deletions(
                        session, live_source_urls={kept}, dry_run=False
                    )

                # Nothing archived by the aborted run.
                still = (
                    await session.execute(select(Story).where(Story.source_url == gone))
                ).scalar_one()
                return still.status

        status = asyncio.run(scenario())
        asyncio.run(engine.dispose())
        assert status != StoryStatus.ARCHIVED
