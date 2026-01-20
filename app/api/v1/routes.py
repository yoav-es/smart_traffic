"""API v1 routes for event ingestion and querying."""

from typing import List
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks
from app.api.v1.schemas import EventIn, EventOut
from app.ml.mcp_client import MCPClient
import os
from datetime import datetime as _dt

router = APIRouter(prefix="/v1", tags=["v1"])

# Simple in-memory store for the skeleton stage.
_EVENTS: List[EventOut] = []
_NEXT_ID = 1


@router.get("/health")
async def health() -> dict:
    """Health check endpoint."""
    return {"status": "ok", "service": "smart_traffic"}


@router.post("/events", response_model=EventOut, status_code=201)
async def ingest_event(event: EventIn, background_tasks: BackgroundTasks) -> EventOut:
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

    # schedule background MCP classification (non-blocking)
    async def _run_classification(eid: int, event_payload: dict) -> None:
        # Use configured MCP_URL (defaults to the compose service `http://mcp:8001`)
        client = MCPClient(base_url=os.getenv("MCP_URL", "http://127.0.0.1:8001"))
        try:
            # Send full event payload to the MCP server for classification
            print(f"[background] starting classification for event {eid}")
            resp = await client.classify(event_payload)
            # resp expected to be {"result": {"classification": "...", "score": ...}}
            result = resp.get("result", {})
            print(f"[background] got result for event {eid}: {result}")
            # update in-memory record if present
            for i, rec in enumerate(_EVENTS):
                if rec.id == eid:
                    rec.classification = result.get("classification", rec.classification)
                    rec.processed_at = _dt.utcnow()
                    break
        except Exception:
            # swallow errors for now; in production log/alert
            pass
        finally:
            await client.aclose()

    # pass the event payload to the background task so MCP server does not need DB
    background_tasks.add_task(_run_classification, out.id, out.dict())

    # Walrus operator demonstration and simple memory cap:
    if (n := len(_EVENTS)) > 1000:
        del _EVENTS[0 : n - 1000]

    return out


@router.get("/events", response_model=List[EventOut])
async def list_events(limit: int = 100) -> List[EventOut]:
    """Return the most recent events up to `limit`."""
    return _EVENTS[-limit:]

