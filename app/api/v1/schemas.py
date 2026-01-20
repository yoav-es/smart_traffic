"""Pydantic schemas for API v1."""

from datetime import datetime
from typing import Dict, Optional

from pydantic import BaseModel


class EventIn(BaseModel):
    """Payload for an incoming traffic event."""

    sensor_id: str
    timestamp: datetime
    vehicle_count: int
    avg_speed: float
    metadata: Optional[Dict] = None


class EventOut(EventIn):
    """Response model for stored/processed events."""

    id: int
    processed_at: datetime
    classification: str

