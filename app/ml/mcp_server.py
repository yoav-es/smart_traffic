from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, Optional
import os
import json
import asyncpg
from app.api.v1.schemas import EventIn
from app.ml.classifier import classify

app = FastAPI(title="smart_traffic_mcp", version="0.1.0")


class ClassifyRequest(BaseModel):
    event: Optional[EventIn] = None
    event_id: Optional[int] = None


@app.post("/classify")
async def classify_endpoint(event: EventIn) -> Dict[str, Any]:
    """Classify an event payload directly."""
    result = classify(event.dict())
    return {"result": result}


@app.post("/classify_by_id")
async def classify_by_id(req: ClassifyRequest) -> Dict[str, Any]:
    """
    Classify by event_id by fetching the event from the DB (if configured)
    or classify an event payload if provided.
    """
    if req.event:
        result = classify(req.event.dict())
        return {"result": result}

    if not req.event_id:
        raise HTTPException(status_code=400, detail="provide event or event_id")

    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise HTTPException(status_code=501, detail="DATABASE_URL not configured")


    # Convert SQLAlchemy URL format (postgresql+asyncpg://...) to asyncpg format (postgresql://...)
    # asyncpg doesn't understand the +asyncpg driver specifier
    asyncpg_url = db_url.replace("postgresql+asyncpg://", "postgresql://")

    conn = await asyncpg.connect(asyncpg_url)
    try:
        row = await conn.fetchrow(
            "SELECT id, sensor_id, timestamp, vehicle_count, avg_speed, metadata FROM events WHERE id=$1",
            req.event_id,
        )
        if not row:
            raise HTTPException(status_code=404, detail="event not found")

        event = {
            "sensor_id": row["sensor_id"],
            "timestamp": row["timestamp"].isoformat() if hasattr(row["timestamp"], "isoformat") else str(row["timestamp"]),
            "vehicle_count": row["vehicle_count"],
            "avg_speed": float(row["avg_speed"]),
            "metadata": json.loads(row["metadata"]) if row["metadata"] else None,
        }

        result = classify(event)
        return {"result": result}
    finally:
        await conn.close()
