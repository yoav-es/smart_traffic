# smart_traffic

Minimal backend to ingest traffic sensor data, classify events, and expose via FastAPI.

This skeleton is the first step. It includes:
- Basic FastAPI app with health check and event endpoints
- Minimal in-memory storage (to be replaced by Postgres)
- Docker Compose with Postgres and Redis (services only)
- Tests using `pytest` and `httpx`

Quickstart:
1. Create a virtualenv: `python -m venv .venv && .venv/bin/activate`
2. Install deps: `pip install -r requirements.txt`
3. Run app: `make run`
4. Run tests: `make test`

