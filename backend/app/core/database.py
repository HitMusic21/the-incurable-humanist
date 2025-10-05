"""
Database engine and session management.
"""

import asyncio
import logging
import os

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from .config import settings

logger = logging.getLogger(__name__)

# Create async engine with Railway-optimized pool settings
engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,
    echo=os.getenv("DB_ECHO", "false").lower() == "true",  # Log SQL queries (controlled by DB_ECHO env var)
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


async def test_db_connection() -> bool:
    """
    Test database connectivity during application startup.

    Returns:
        bool: True if connection successful, False otherwise

    Usage:
        Called during app startup to verify asyncpg driver and connection
    """
    try:
        logger.info(f"Testing database connection to: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'database'}")

        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1 as test"))
            row = result.fetchone()

            if row and row[0] == 1:
                logger.info("✓ Database connection test successful (asyncpg driver working)")
                logger.info(f"✓ Driver: {engine.driver}")
                logger.info(f"✓ Dialect: {engine.dialect.name}")
                return True
            else:
                logger.error("✗ Database connection test failed: unexpected result")
                return False

    except Exception as e:
        logger.error(f"✗ Database connection test failed: {e}")
        logger.error(f"  DATABASE_URL pattern: postgresql+asyncpg://...")
        logger.error(f"  Ensure asyncpg is installed and DATABASE_URL uses +asyncpg driver")
        return False


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
    # First, test the connection to verify asyncpg driver is working
    logger.info("=" * 60)
    logger.info("DATABASE CONNECTIVITY TEST")
    logger.info("=" * 60)

    connection_test = await test_db_connection()

    if not connection_test:
        logger.error("Initial database connection test failed!")
        logger.error("Please verify DATABASE_URL uses postgresql+asyncpg:// driver")
        raise RuntimeError("Database connection test failed - check DATABASE_URL and asyncpg installation")

    logger.info("=" * 60)

    max_retries = 10
    base_delay = 1.5

    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"Database initialization attempt {attempt}/{max_retries}")

            async with engine.begin() as conn:
                # Import all models to register them with SQLModel
                from app.models import (
                    Bookmark,
                    Comment,
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
                raise RuntimeError(f"Database initialization failed after {max_retries} attempts: {e}")

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
