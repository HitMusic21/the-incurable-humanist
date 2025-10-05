"""
Database engine and session management.
"""

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from .config import settings

# Create async engine
engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,
    echo=True,  # Log SQL queries (disable in production)
    future=True,
)

# Create async session factory
async_session_maker = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db() -> None:
    """
    Initialize database tables.
    Creates all tables defined in SQLModel models.
    """
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
