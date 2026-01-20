"""Async SQLAlchemy database setup for smart_traffic.

This module provides the database connection pool, session factory, and
dependency injection for async database operations throughout the application.
"""

import os
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

# Database URL from environment variable
# Format: postgresql+asyncpg://user:password@host:port/database
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/smart_traffic"
)

# Create async engine with connection pooling
# echo=True enables SQL query logging for debugging
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL query logging in development
    future=True,
    pool_pre_ping=True,  # Verify connections before using
)

# Create async session factory
# expire_on_commit=False allows accessing objects after commit
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Base class for declarative SQLAlchemy models
Base = declarative_base()


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency function to provide database session to FastAPI routes.

    This function is used as a FastAPI dependency (Depends(get_session)).
    It creates a new database session for each request and ensures proper
    cleanup after the request completes.

    Yields:
        AsyncSession: Database session for the current request

    Example:
        ```python
        @router.get("/items")
        async def get_items(session: AsyncSession = Depends(get_session)):
            result = await session.execute(select(Item))
            return result.scalars().all()
        ```
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
