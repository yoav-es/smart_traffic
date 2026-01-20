"""API v1 routes for event ingestion and querying."""

from typing import List
from datetime import datetime

from fastapi import APIRouter
from app.api.v1.schemas import EventIn, EventOut

router = APIRouter(prefix="/v1", tags=["v1"])

# Simple in-memory store for the skeleton stage.
_EVENTS: List[EventOut] = []
_NEXT_ID = 1


@router.get("/health")
async def health() -> dict:
    """Health check endpoint."""
    return {"status": "ok", "service": "smart_traffic"}


@router.post("/events", response_model=EventOut, status_code=201)
async def ingest_event(event: EventIn) -> EventOut:
    """
    Ingest a traffic sensor event, perform a trivial classification,
    store in-memory and return the processed record.

    This function is intentionally simple for the skeleton stage.
    """
    global _NEXT_ID

    # Simple placeholder classification logic.
    classification = "low" if event.vehicle_count < 5 else "high"
    processed_at = datetime.utcnow()

    out = EventOut(
        id=_NEXT_ID,
        sensor_id=event.sensor_id,
        timestamp=event.timestamp,
        vehicle_count=event.vehicle_count,
        avg_speed=event.avg_speed,
        metadata=event.metadata,
        processed_at=processed_at,
        classification=classification,
    )

    _EVENTS.append(out)
    _NEXT_ID += 1

    # Walrus operator demonstration and simple memory cap:
    if (n := len(_EVENTS)) > 1000:
        del _EVENTS[0 : n - 1000]

    return out


@router.get("/events", response_model=List[EventOut])
async def list_events(limit: int = 100) -> List[EventOut]:
    """Return the most recent events up to `limit`."""
    return _EVENTS[-limit:]

