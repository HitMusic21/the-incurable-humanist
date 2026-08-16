"""
Database engine and session management.
"""

import asyncio
import logging
import os

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from .config import settings

logger = logging.getLogger(__name__)

# Create async engine with Railway-optimized pool settings
engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,
    # Log SQL queries when DB_ECHO=true.
    echo=os.getenv("DB_ECHO", "false").lower() == "true",
    future=True,
    pool_pre_ping=True,  # Verify connections before using
    pool_size=5,  # Connection pool size
    max_overflow=5,  # Max overflow connections
)

# Create async session factory
async_session_maker = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def db_ping() -> bool:
    """
    Ping database to verify connectivity.

    Returns:
        bool: True if database is reachable, False otherwise

    Usage:
        Used by /ready endpoint for Railway health checks
    """
    try:
        async with engine.connect() as conn:
            await conn.exec_driver_sql("SELECT 1")
        return True
    except Exception as e:
        logger.warning("DB ping failed: %s", e)
        return False


async def init_db() -> None:
    """
    Initialize database tables with retry logic.
    Creates all tables defined in SQLModel models.

    Retries: 10 attempts with exponential backoff (1.5s base delay)

    Raises:
        RuntimeError: If unable to connect after all retries
    """
    max_retries = 10
    base_delay = 1.5

    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"Database initialization attempt {attempt}/{max_retries}")

            # Probe inside the loop so a cold-start blip retries with backoff
            # instead of crash-looping the container before the first attempt.
            if not await db_ping():
                raise Exception("Database not reachable")

            async with engine.begin() as conn:
                # Import all models INSIDE the function so SQLModel.metadata
                # sees every table. Ruff would strip these as unused — the
                # noqa keeps them; they're load-bearing side-effect imports.
                from app.models import (  # noqa: F401
                    Bookmark,
                    Comment,
                    LeadCapture,
                    LeadEvent,
                    NewsletterSubscription,
                    ReadingProgress,
                    Story,
                    StoryTheme,
                    Theme,
                    User,
                )

                # Create all tables
                await conn.run_sync(SQLModel.metadata.create_all)

            logger.info("✓ Database initialized successfully")
            return

        except Exception as e:
            logger.warning(f"Database initialization attempt {attempt} failed: {e}")

            if attempt == max_retries:
                logger.error("Max retries reached. Unable to initialize database.")
                raise RuntimeError(
                    f"Database initialization failed after {max_retries} attempts: {e}"
                ) from e

            # Exponential backoff
            delay = base_delay * (1.5 ** (attempt - 1))
            logger.info(f"Retrying in {delay:.1f}s...")
            await asyncio.sleep(delay)


async def get_session() -> AsyncSession:
    """
    Dependency to get async database session.

    Yields:
        AsyncSession: Database session

    Usage:
        @app.get("/items")
        async def get_items(session: AsyncSession = Depends(get_session)):
            ...
    """
    async with async_session_maker() as session:
        yield session
