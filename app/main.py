"""FastAPI application entrypoint for smart_traffic."""

from fastapi import FastAPI
from app.api.v1 import routes as v1_routes

app = FastAPI(title="smart_traffic", version="0.1.0")


@app.on_event("startup")
async def on_startup() -> None:
    """Tasks to run on startup (placeholder)."""
    # e.g., initialize connections to DB/Redis here in later steps
    return None


@app.on_event("shutdown")
async def on_shutdown() -> None:
    """Tasks to run on shutdown (placeholder)."""
    # e.g., close connections
    return None


app.include_router(v1_routes.router)

