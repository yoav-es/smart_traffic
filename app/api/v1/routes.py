"""API v1 routes for event ingestion and querying.

This module handles HTTP endpoints for traffic event ingestion and retrieval.
It uses async database operations and background tasks for MCP classification.
"""

import os
import logging
from typing import List
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas import EventIn, EventOut
from app.db import get_session, AsyncSessionLocal
from app.models import Event
from app.ml.mcp_client import MCPClient

# Configure logging for background tasks
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1", tags=["v1"])


@router.get("/health")
async def health() -> dict:
    """Health check endpoint."""
    return {"status": "ok", "service": "smart_traffic"}


@router.post("/events", response_model=EventOut, status_code=201)
async def ingest_event(
    event: EventIn,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
) -> EventOut:
    """
    Ingest a traffic sensor event, store in database, and schedule MCP classification.

    This endpoint performs the following operations:
    1. Creates an initial classification (placeholder)
    2. Stores the event in the database
    3. Schedules an async background task for MCP classification
    4. Returns the stored event immediately

    The background task will update the classification asynchronously without
    blocking the HTTP response. If the MCP service is unavailable, the event
    remains stored with the initial classification.

    Args:
        event: Event data from the request body
        background_tasks: FastAPI background tasks manager
        session: Database session (injected by dependency)

    Returns:
        EventOut: The created event record with initial classification

    Raises:
        HTTPException: If database operation fails (500)
    """
    try:
        # Initial placeholder classification (will be updated by MCP)
        classification = "low" if event.vehicle_count < 5 else "high"
        processed_at = datetime.utcnow()

        # Create database record
        db_event = Event(
            sensor_id=event.sensor_id,
            timestamp=event.timestamp,
            vehicle_count=event.vehicle_count,
            avg_speed=event.avg_speed,
            event_metadata=event.metadata,  # Map schema.metadata to model.event_metadata
            processed_at=processed_at,
            classification=classification,
        )

        session.add(db_event)
        await session.commit()
        await session.refresh(db_event)

        # Convert to response model
        out = EventOut(
            id=db_event.id,
            sensor_id=db_event.sensor_id,
            timestamp=db_event.timestamp,
            vehicle_count=db_event.vehicle_count,
            avg_speed=db_event.avg_speed,
            metadata=db_event.event_metadata,  # Map model.event_metadata back to schema.metadata
            processed_at=db_event.processed_at,
            classification=db_event.classification,
        )

        # Schedule background MCP classification (non-blocking)
        # This runs asynchronously and won't affect the HTTP response time
        background_tasks.add_task(_run_classification, out.id, out.dict())

        return out

    except Exception as e:
        # Rollback on error to prevent partial state
        await session.rollback()
        logger.error(f"Failed to ingest event: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Failed to store event"
        ) from e


async def _run_classification(event_id: int, event_payload: dict) -> None:
    """
    Background task to classify event via MCP server and update database.

    This function runs asynchronously in the background after the HTTP response
    is sent. It handles errors gracefully to prevent crashing the application.

    Args:
        event_id: Database ID of the event to update
        event_payload: Full event payload to send to MCP server
    """
    mcp_url = os.getenv("MCP_URL", "http://127.0.0.1:8001")
    client = MCPClient(base_url=mcp_url)

    try:
        logger.info(f"Starting MCP classification for event {event_id}")

        # Call MCP server for classification
        resp = await client.classify(event_payload)
        result = resp.get("result", {})

        logger.info(
            f"Received MCP classification for event {event_id}: "
            f"{result.get('classification', 'unknown')}"
        )

        # Update database record with MCP classification
        # Use separate session for background task (session from request is closed)
        async with AsyncSessionLocal() as update_session:
            try:
                stmt = select(Event).where(Event.id == event_id)
                result_query = await update_session.execute(stmt)
                db_event = result_query.scalar_one_or_none()

                if db_event:
                    # Update classification if MCP provided one
                    new_classification = result.get("classification")
                    if new_classification:
                        db_event.classification = new_classification
                        db_event.processed_at = datetime.utcnow()
                        await update_session.commit()
                        logger.info(f"Updated event {event_id} classification to {new_classification}")
                    else:
                        logger.warning(f"MCP returned no classification for event {event_id}")
                else:
                    logger.warning(f"Event {event_id} not found for classification update")

            except Exception as db_error:
                await update_session.rollback()
                logger.error(
                    f"Failed to update event {event_id} classification: {db_error}",
                    exc_info=True
                )

    except Exception as e:
        # Log error but don't crash - event remains with initial classification
        logger.error(
            f"Background classification failed for event {event_id}: {e}",
            exc_info=True
        )
    finally:
        await client.aclose()


@router.get("/events", response_model=List[EventOut])
async def list_events(
    limit: int = 100, session: AsyncSession = Depends(get_session)
) -> List[EventOut]:
    """
    Retrieve the most recent events from the database.

    Args:
        limit: Maximum number of events to return (default: 100, max: 1000)
        session: Database session (injected by dependency)

    Returns:
        List of EventOut objects, ordered by ID descending (most recent first)

    Raises:
        HTTPException: If database query fails (500)
    """
    # Enforce maximum limit to prevent excessive queries
    if limit > 1000:
        limit = 1000
    if limit < 1:
        limit = 1

    try:
        # Query events ordered by ID descending (most recent first)
        stmt = select(Event).order_by(desc(Event.id)).limit(limit)
        result = await session.execute(stmt)
        events = result.scalars().all()

        # Convert SQLAlchemy models to Pydantic schemas
        return [
            EventOut(
                id=event.id,
                sensor_id=event.sensor_id,
                timestamp=event.timestamp,
                vehicle_count=event.vehicle_count,
                avg_speed=event.avg_speed,
                metadata=event.event_metadata,  # Map model.event_metadata back to schema.metadata
                processed_at=event.processed_at,
                classification=event.classification,
            )
            for event in events
        ]

    except Exception as e:
        logger.error(f"Failed to retrieve events: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Failed to retrieve events"
        ) from e

