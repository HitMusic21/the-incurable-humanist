"""
Shared test fixtures.

The problem this file solves: `app.core.database` builds an async `engine` at
import time bound to whatever event loop first touches it. With a sync
`TestClient` and Postgres+asyncpg, each test starts + tears down its own loop
(TestClient uses anyio's blocking portal internally). The connection pool
holds a Future on the previous loop → "attached to a different loop" errors
across cases.

Two fixes stacked:
  1. Override `get_session` with a per-test async engine that uses NullPool
     (no cross-request connection reuse) — connections open/close within a
     single request, so nothing leaks between TestClient invocations.
  2. Do setup/teardown (truncate) with a **sync** psycopg-style engine so it
     never touches the async loop machinery at all.

Requires a reachable Postgres (docker-compose db). Set DATABASE_URL to point
at it — the docker-compose host mapping is `localhost:5433` by default.
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app.core.database import get_session as _real_get_session


def _async_url() -> str:
    """asyncpg-flavored URL for the app's session dependency."""
    raw = os.getenv("DATABASE_URL") or "postgresql+asyncpg://postgres:postgres@localhost:5433/tih_db"
    if "+asyncpg" not in raw:
        raw = raw.replace("postgresql://", "postgresql+asyncpg://").replace(
            "postgres://", "postgresql+asyncpg://"
        )
    return raw


def _sync_url() -> str:
    """psycopg2 URL for sync setup/teardown — avoids any async loop entanglement."""
    return (
        _async_url()
        .replace("postgresql+asyncpg://", "postgresql+psycopg2://")
        .replace("+asyncpg", "+psycopg2")
    )


# Order matters — child tables first (FK constraints). CASCADE covers the rest.
_TRUNCATE_TABLES: tuple[str, ...] = (
    "lead_event",
    "lead_capture",
    "story",
    "newslettersubscription",
    "readingprogress",
    "comment",
    "bookmark",
    "user",
)


@pytest.fixture(autouse=True)
def _clean_db_between_tests():
    """
    Sync-engine TRUNCATE between tests. Uses psycopg2 (installed via SQLAlchemy)
    so it lives entirely outside the asyncio world. Wrapped in try/except so
    a missing table (schema older than expected) doesn't block the suite.
    """
    engine = create_engine(_sync_url(), poolclass=NullPool)
    try:
        with engine.begin() as conn:
            for table in _TRUNCATE_TABLES:
                try:
                    conn.execute(text(f'TRUNCATE TABLE "{table}" RESTART IDENTITY CASCADE'))
                except Exception:  # noqa: BLE001
                    # Table may not exist yet on a fresh DB; carry on.
                    pass
    finally:
        engine.dispose()
    yield


@pytest.fixture(autouse=True)
def _override_get_session():
    """
    Rebind app.dependency_overrides so every handler gets a session from a
    NullPool async engine created inline. NullPool means: open a connection
    per request, close it when the request finishes. No cross-request pooling
    → no "attached to a different loop" leaks.
    """
    from app.main import app

    engine = create_async_engine(_async_url(), poolclass=NullPool, future=True)
    session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def _override() -> AsyncIterator[AsyncSession]:
        async with session_maker() as session:
            yield session

    app.dependency_overrides[_real_get_session] = _override
    yield
    app.dependency_overrides.pop(_real_get_session, None)
    # Engine dispose is best-effort — the loop it was created on may already
    # be closed by TestClient teardown. Swallow.
    try:
        import asyncio

        loop = asyncio.new_event_loop()
        loop.run_until_complete(engine.dispose())
        loop.close()
    except Exception:  # noqa: BLE001
        pass
