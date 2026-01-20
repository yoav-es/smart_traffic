"""FastAPI application entrypoint for smart_traffic.

This module initializes the FastAPI application, sets up database connections,
and registers API routes. It handles application lifecycle events (startup/shutdown)
to ensure proper resource management.
"""

import logging

from fastapi import FastAPI

from app.api.v1 import routes as v1_routes

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(title="smart_traffic", version="0.1.0")


@app.on_event("startup")
async def on_startup() -> None:
    """
    Initialize database connections and create tables on application startup.
    
    This function is a placeholder for future DB initialization.
    Currently using in-memory storage.
    """
    try:
        # Try to import and initialize DB if modules exist
        try:
            from app.db import engine, Base
            from app.models import Event  # noqa: F401

            # Create tables if they don't exist
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables initialized successfully")
        except ImportError:
            logger.info("DB modules not available, using in-memory storage")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}", exc_info=True)
        # Don't raise - allow app to start even if DB init fails


@app.on_event("shutdown")
async def on_shutdown() -> None:
    """
    Close database connections on application shutdown.
    """
    try:
        try:
            from app.db import engine
            await engine.dispose()
            logger.info("Database connections closed")
        except ImportError:
            pass  # No DB to close
    except Exception as e:
        logger.error(f"Error during shutdown: {e}", exc_info=True)


# Register API routes
app.include_router(v1_routes.router)

