"""Async API tests for the skeleton using httpx and pytest-asyncio."""

import os
from datetime import datetime, timezone
from typing import AsyncGenerator

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.main import app
from app.db import Base, get_session
from app.models import Event  # noqa: F401


# Test database URL (Postgres for testing)
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/smart_traffic_test"
)


@pytest.fixture
async def test_engine():
    """Create a test database engine."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def test_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async_session_maker = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session_maker() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def client(test_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create a test client with overridden database dependency."""

    async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
        yield test_session

    app.dependency_overrides[get_session] = override_get_session

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_health(client: AsyncClient) -> None:
    """Test health check endpoint."""
    response = await client.get("/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_ingest_and_list(client: AsyncClient) -> None:
    """Test event ingestion and listing."""
    payload = {
        "sensor_id": "s1",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "vehicle_count": 3,
        "avg_speed": 45.2,
        "metadata": {"lane": 1},
    }
    post_resp = await client.post("/v1/events", json=payload)
    assert post_resp.status_code == 201
    body = post_resp.json()
    assert body["sensor_id"] == "s1"
    assert body["classification"] == "low"
    assert "id" in body

    list_resp = await client.get("/v1/events")
    assert list_resp.status_code == 200
    events = list_resp.json()
    assert len(events) >= 1
    assert events[0]["sensor_id"] == "s1"

