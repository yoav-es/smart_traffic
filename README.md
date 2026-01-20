# smart_traffic

Backend service to ingest traffic sensor data, classify events via MCP server, and expose via FastAPI.

## Features

- FastAPI application with health check and event ingestion endpoints
- Async PostgreSQL database layer using SQLAlchemy
- Model Context Protocol (MCP) server for event classification
- Background task processing for non-blocking MCP classification
- Docker Compose setup with Postgres, Redis, and MCP services
- DevContainer configuration for container-based development
- Tests using `pytest` and `httpx`

## Quickstart

### Using Docker Compose (Recommended)

```bash
# Start all services
docker compose up -d --build

# View logs
docker compose logs -f app

# Run tests
docker compose exec app python -m pytest -v

# Stop services
docker compose down
```

### Local Development

1. Create a virtualenv: `python -m venv .venv && .venv/bin/activate`
2. Install deps: `pip install -r requirements.txt`
3. Ensure Postgres and Redis are running (or use Docker Compose)
4. Set environment variables:
   - `DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/smart_traffic`
   - `MCP_URL=http://localhost:8001`
   - `REDIS_URL=redis://localhost:6379/0`
5. Run app: `make run` or `uvicorn app.main:app --reload`
6. Run tests: `make test`

## Architecture

- **FastAPI App** (`app/main.py`): Main API service on port 8000
- **MCP Server** (`app/ml/mcp_server.py`): Classification service on port 8001
- **Database**: PostgreSQL with async SQLAlchemy ORM
- **Background Tasks**: FastAPI background tasks for async MCP classification

## API Endpoints

- `GET /v1/health` - Health check
- `POST /v1/events` - Ingest traffic sensor event
- `GET /v1/events` - List recent events

