"""SQLAlchemy models for smart_traffic.

This module defines the database schema using SQLAlchemy ORM models.
Each model class corresponds to a database table.
"""

from sqlalchemy import JSON, Column, DateTime, Float, Integer, String
from sqlalchemy.sql import func

from app.db import Base


class Event(Base):
    """
    Event model representing traffic sensor events in the database.

    This model matches the EventOut Pydantic schema and represents a single
    traffic event with sensor data, vehicle metrics, and classification results.

    Attributes:
        id: Primary key, auto-incrementing integer
        sensor_id: Identifier for the sensor that generated the event
        timestamp: When the event occurred (timezone-aware)
        vehicle_count: Number of vehicles detected
        avg_speed: Average speed of vehicles (float)
        metadata: Optional JSON metadata (dict)
        processed_at: When the event was processed/stored
        classification: Traffic classification result ("low", "medium", "high", or "pending")

    Indexes:
        - id (primary key, auto-indexed)
        - sensor_id (for filtering by sensor)
        - timestamp (for time-based queries)
    """

    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    sensor_id = Column(String, nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    vehicle_count = Column(Integer, nullable=False)
    avg_speed = Column(Float, nullable=False)
    event_metadata = Column("metadata", JSON, nullable=True)  # Column named "metadata" in DB, attribute is event_metadata
    processed_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()  # Default to current timestamp
    )
    classification = Column(String, nullable=False, default="pending")

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"<Event(id={self.id}, sensor_id={self.sensor_id}, "
            f"classification={self.classification})>"
        )
