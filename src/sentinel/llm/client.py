"""Ollama HTTP client for local LLM inference."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

import httpx
import structlog

from sentinel.exceptions import (
    InferenceConnectionError,
    InferenceError,
    InferenceTimeout,
)
from sentinel.llm.prompts import SYSTEM_ACADEMIC
from sentinel.settings import LlmCfg

log = structlog.get_logger(__name__)


class InferenceClient:
    """Async wrapper around the Ollama ``/api/generate``."""

    def __init__(
        self,
        host: str,
        model: str,
        timeout: int,
    ) -> None:
        self._host = host.rstrip("/")
        self._model = model
        self._http = httpx.AsyncClient(
            base_url=self._host,
            timeout=httpx.Timeout(float(timeout)),
        )

    # -- generation -----------------------------------------------

    async def generate(
        self,
        prompt: str,
        *,
        system: str = SYSTEM_ACADEMIC,
        temperature: float = 0.0,
    ) -> str:
        """Blocking (non-streaming) generation."""
        payload: dict[str, Any] = {
            "model": self._model,
            "prompt": prompt,
            "system": system,
            "stream": False,
            "options": {"temperature": temperature},
        }
        data = await self._post("/api/generate", payload)
        return str(data.get("response", ""))

    async def generate_stream(
        self,
        prompt: str,
        *,
        system: str = SYSTEM_ACADEMIC,
        temperature: float = 0.0,
    ) -> AsyncIterator[str]:
        """Streaming generation — yields text tokens."""
        payload: dict[str, Any] = {
            "model": self._model,
            "prompt": prompt,
            "system": system,
            "stream": True,
            "options": {"temperature": temperature},
        }
        try:
            async with self._http.stream(
                "POST",
                "/api/generate",
                json=payload,
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line:
                        continue
                    import json

                    chunk = json.loads(line)
                    token = chunk.get("response", "")
                    if token:
                        yield token
                    if chunk.get("done"):
                        break
        except httpx.ConnectError as exc:
            raise InferenceConnectionError(str(exc)) from exc
        except httpx.ReadTimeout as exc:
            raise InferenceTimeout(str(exc)) from exc

    # -- health ---------------------------------------------------

    async def check_health(self) -> dict[str, str]:
        """Ping the Ollama service."""
        try:
            r = await self._http.get("/api/version")
            r.raise_for_status()
            return {
                "status": "healthy",
                "version": r.json().get("version", ""),
            }
        except Exception as exc:
            return {
                "status": "unhealthy",
                "error": str(exc),
            }

    # -- internal -------------------------------------------------

    async def _post(
        self, path: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        try:
            resp = await self._http.post(path, json=payload)
            resp.raise_for_status()
            result: dict[str, Any] = resp.json()
            return result
        except httpx.ConnectError as exc:
            log.error("ollama_unreachable", err=str(exc))
            raise InferenceConnectionError(str(exc)) from exc
        except httpx.ReadTimeout as exc:
            log.error("ollama_timeout", err=str(exc))
            raise InferenceTimeout(str(exc)) from exc
        except httpx.HTTPStatusError as exc:
            log.error(
                "ollama_http_error",
                status=exc.response.status_code,
            )
            raise InferenceError(f"HTTP {exc.response.status_code}") from exc

    async def close(self) -> None:
        await self._http.aclose()


def create_inference_client(
    cfg: LlmCfg,
) -> InferenceClient:
    """Factory: build an ``InferenceClient``."""
    return InferenceClient(
        host=cfg.host,
        model=cfg.model,
        timeout=cfg.timeout,
    )
