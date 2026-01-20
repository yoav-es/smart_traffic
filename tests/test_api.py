"""Async API tests for the skeleton using httpx and pytest-asyncio."""

from datetime import datetime, timezone

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest.mark.asyncio
async def test_health() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_ingest_and_list() -> None:
    payload = {
        "sensor_id": "s1",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "vehicle_count": 3,
        "avg_speed": 45.2,
        "metadata": {"lane": 1},
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        post_resp = await ac.post("/v1/events", json=payload)
        assert post_resp.status_code == 201
        body = post_resp.json()
        assert body["sensor_id"] == "s1"
        assert body["classification"] == "low"

        list_resp = await ac.get("/v1/events")
        assert list_resp.status_code == 200
        assert len(list_resp.json()) >= 1

