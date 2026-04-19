"""Thin async client around Ollama's /api/chat endpoint.

Ollama runs on the same machine (localhost:11434). All model selection is
per-request — Ollama transparently swaps models in/out of VRAM as needed.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from app.config import get_settings

log = logging.getLogger(__name__)


ToolSpec = dict[str, Any]
Message = dict[str, Any]


class OllamaClient:
    def __init__(self, base_url: str | None = None, timeout_s: int | None = None) -> None:
        s = get_settings()
        self.base_url = (base_url or s.ollama_base_url).rstrip("/")
        self.timeout = timeout_s or s.ollama_timeout_s

    async def chat(
        self,
        *,
        model: str,
        messages: list[Message],
        tools: list[ToolSpec] | None = None,
        temperature: float = 0.2,
        stream: bool = False,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": stream,
            "options": {"temperature": temperature},
        }
        if tools:
            payload["tools"] = tools

        async with httpx.AsyncClient(timeout=self.timeout) as http:
            resp = await http.post(f"{self.base_url}/api/chat", json=payload)
            resp.raise_for_status()
            return resp.json()

    async def list_models(self) -> list[str]:
        async with httpx.AsyncClient(timeout=10) as http:
            resp = await http.get(f"{self.base_url}/api/tags")
            resp.raise_for_status()
            data = resp.json()
            return [m["name"] for m in data.get("models", [])]

    async def health(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=3) as http:
                resp = await http.get(f"{self.base_url}/api/tags")
                return resp.status_code == 200
        except Exception as exc:
            log.warning("ollama health check failed: %s", exc)
            return False
