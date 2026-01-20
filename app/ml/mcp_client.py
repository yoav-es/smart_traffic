import os
from typing import Any, Dict, Optional

import httpx

MCP_URL = os.getenv("MCP_URL", "http://mcp:8001")


class MCPClient:
    def __init__(self, base_url: Optional[str] = None, timeout: float = 5.0):
        self.base_url = base_url or MCP_URL
        self._client = httpx.AsyncClient(timeout=timeout)

    async def classify(self, event: Dict[str, Any]) -> Dict[str, Any]:
        resp = await self._client.post(f"{self.base_url}/classify", json=event)
        resp.raise_for_status()
        return resp.json()

    async def classify_by_id(self, event_id: int) -> Dict[str, Any]:
        resp = await self._client.post(f"{self.base_url}/classify_by_id", json={"event_id": event_id})
        resp.raise_for_status()
        return resp.json()

    async def aclose(self) -> None:
        await self._client.aclose()