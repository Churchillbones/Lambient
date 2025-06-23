from __future__ import annotations

import asyncio
from typing import Any, Dict

import requests


class APIClient:  # noqa: D401
    """Minimal async helper for blocking HTTP requests inside async flows."""

    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    # ------------------------------------------------------------------
    async def post(self, path: str, json: Dict[str, Any], timeout: int = 30) -> Dict[str, Any]:  # noqa: D401
        def _sync_post():
            url = f"{self.base_url}{path}"
            resp = requests.post(url, json=json, timeout=timeout)
            resp.raise_for_status()
            return resp.json()

        return await asyncio.to_thread(_sync_post) 