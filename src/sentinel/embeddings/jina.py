"""Jina AI embedding client (v3 model, 1024-dim)."""

from __future__ import annotations

import httpx
import structlog

from sentinel.exceptions import EmbeddingError

log = structlog.get_logger(__name__)

_API_URL = "https://api.jina.ai/v1/embeddings"
_MODEL = "jina-embeddings-v3"
_BATCH_SIZE = 100


class EmbeddingProvider:
    """Generate dense vector embeddings via Jina AI."""

    def __init__(
        self,
        api_key: str,
        *,
        batch_size: int = _BATCH_SIZE,
    ) -> None:
        if not api_key:
            raise EmbeddingError("JINA_API_KEY is required")
        self._key = api_key
        self._batch = batch_size
        self._http = httpx.AsyncClient(
            timeout=60.0,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )

    async def embed_query(self, text: str) -> list[float]:
        """Embed a single search query."""
        vecs = await self._call([text], task="retrieval.query")
        return vecs[0]

    async def embed_passages(self, texts: list[str]) -> list[list[float]]:
        """Embed document passages in batches."""
        all_vecs: list[list[float]] = []
        for i in range(0, len(texts), self._batch):
            batch = texts[i : i + self._batch]
            vecs = await self._call(batch, task="retrieval.passage")
            all_vecs.extend(vecs)
        return all_vecs

    async def _call(
        self,
        inputs: list[str],
        task: str,
    ) -> list[list[float]]:
        payload = {
            "model": _MODEL,
            "input": inputs,
            "task": task,
        }
        try:
            resp = await self._http.post(_API_URL, json=payload)
            resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            log.error(
                "jina_http_error",
                status=exc.response.status_code,
            )
            raise EmbeddingError(
                f"Jina API {exc.response.status_code}"
            ) from exc
        except httpx.RequestError as exc:
            log.error("jina_request_error", err=str(exc))
            raise EmbeddingError(str(exc)) from exc

        data = resp.json().get("data", [])
        data.sort(key=lambda d: d["index"])
        return [d["embedding"] for d in data]

    async def close(self) -> None:
        await self._http.aclose()


def create_embedding_provider(
    api_key: str,
) -> EmbeddingProvider:
    """Factory: build an ``EmbeddingProvider``."""
    return EmbeddingProvider(api_key)
