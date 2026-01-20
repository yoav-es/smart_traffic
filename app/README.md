# smart_traffic Project Status & Next Steps

## Project Goal
Build a FastAPI backend that ingests traffic sensor data, stores it in Postgres, classifies events via an MCP (Model Context Protocol) server, and exposes results through async background processing.

## Architecture
- **FastAPI app** (`app/main.py`) — main API service
- **MCP server** (`app/ml/mcp_server.py`) — separate HTTP service for classification
- **MCP client** (`app/ml/mcp_client.py`) — async HTTP client to call MCP server
- **Postgres** — event storage (async SQLAlchemy, not yet implemented)
- **Redis** — optional caching (not yet implemented)

## Completed Steps

### Step 1: Skeleton & Tests ✅
- Basic FastAPI app with `/v1/health`, `/v1/events` endpoints
- In-memory event storage (to be replaced by DB)
- Tests passing (pytest — 2 tests)

### Step 2: MCP Infrastructure ✅
- Classifier module (`app/ml/classifier.py`) — rule-based `classify(event)` function
- MCP Server (`app/ml/mcp_server.py`) — FastAPI server with:
  - `POST /classify` — accepts event payload, returns classification
  - `POST /classify_by_id` — fetches event from DB by ID (requires DB layer)
- MCP Client (`app/ml/mcp_client.py`) — async HTTP client wrapper
- Background integration — `POST /v1/events` schedules BackgroundTasks job to call MCP server

### Step 3: Docker & Devcontainer ✅
- `docker-compose.yml` — app, db (Postgres), redis services
- `.devcontainer/devcontainer.json` — compose-based devcontainer
- Dependencies installed: asyncpg, httpx, sqlalchemy, etc.

## Current Status
- ✅ Tests pass: `docker compose exec app python -m pytest -q` → 2 passed
- ✅ MCP server can be started: `uvicorn app.ml.mcp_server:app --host 0.0.0.0 --port 8001`
- ✅ API endpoints work: `GET /v1/health`, `POST /v1/events`, `GET /v1/events`
- ⚠️ Background MCP classification: implemented but needs E2E verification
- ⚠️ IDE import warnings: resolved when using devcontainer Python interpreter

## Next Steps (In Order)

### Step 4: Async DB Layer (Next)
- Create `app/db.py` — async SQLAlchemy engine & session factory
- Create `app/models.py` — Event SQLAlchemy model matching EventOut schema
- Set up Alembic — migrations for events table
- Update `app/api/v1/routes.py` — replace in-memory `_EVENTS` with DB CRUD
- Add test DB fixtures — update `tests/test_api.py` to use test database

### Step 5: MCP Server DB Integration
- Update MCP server `classify_by_id` to use SQLAlchemy async session (replace raw asyncpg)
- Test MCP server can fetch events from Postgres

### Step 6: Background Classification Verification
- E2E test: POST event → verify background task calls MCP → verify DB updated
- Add error handling/logging for background tasks

### Step 7: Optional Enhancements
- Redis caching for `GET /v1/events`
- CI workflow (GitHub Actions)
- Additional tests (edge cases, MCP client/server unit tests)

## Quick Commands Reference

```bash
# Start services
docker compose up -d --build

# Run tests
docker compose exec app python -m pytest -q

# Start MCP server (separate container)
docker run -d --name mcp --network smart_traffic_default smart_traffic-app \
  uvicorn app.ml.mcp_server:app --host 0.0.0.0 --port 8001

# Check logs
docker compose logs app
docker logs mcp

# Rebuild after code changes
docker compose up -d --build
```

## Files Structure
```
smart_traffic/
├── app/
│   ├── main.py              # FastAPI app entrypoint
│   ├── api/v1/
│   │   ├── routes.py        # API endpoints (POST/GET /v1/events)
│   │   └── schemas.py       # Pydantic models (EventIn, EventOut)
│   └── ml/
│       ├── classifier.py    # Rule-based classification logic
│       ├── mcp_server.py    # MCP HTTP server
│       └── mcp_client.py    # MCP HTTP client
├── tests/
│   └── test_api.py          # API tests
├── docker-compose.yml       # Services: app, db, redis
├── Dockerfile               # Python 3.11-slim base
├── requirements.txt        # Dependencies
└── .devcontainer/
    └── devcontainer.json    # VS Code/Cursor devcontainer config
```

## Current Implementation Notes
- **In-memory storage**: `_EVENTS` list in `routes.py` (temporary, will be replaced by DB)
- **MCP URL**: Configured via `MCP_URL` env var (defaults to `http://mcp:8001`)
- **Background tasks**: FastAPI BackgroundTasks (in-process, simple for now)
- **Classification**: Currently returns placeholder "low"/"high" based on `vehicle_count < 5`

Ready to proceed with Step 4 (Async DB Layer) when you are.
