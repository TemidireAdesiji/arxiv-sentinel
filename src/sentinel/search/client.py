"""OpenSearch client for indexing and retrieval."""

from __future__ import annotations

from typing import Any

import structlog
from opensearchpy import OpenSearch

from sentinel.exceptions import (
    IndexCreationError,
    SearchEngineError,
)
from sentinel.search.queries import DslBuilder
from sentinel.search.schema import (
    build_chunk_mapping,
    build_rrf_pipeline,
)
from sentinel.settings import SearchCfg

log = structlog.get_logger(__name__)


class SearchEngine:
    """Manages an OpenSearch connection for hybrid search."""

    def __init__(
        self,
        client: OpenSearch,
        cfg: SearchCfg,
    ) -> None:
        self._os = client
        self._cfg = cfg
        self._chunk_idx = f"{cfg.index}{cfg.chunk_suffix}"

    # -- index lifecycle ------------------------------------------

    def ensure_index(self) -> None:
        """Create the chunk index + RRF pipeline if absent."""
        try:
            self._ensure_rrf_pipeline()
            if self._os.indices.exists(self._chunk_idx):
                log.info(
                    "index_exists",
                    index=self._chunk_idx,
                )
                return
            body = build_chunk_mapping(
                vector_dim=self._cfg.vector_dim,
                space=self._cfg.space_type,
            )
            self._os.indices.create(index=self._chunk_idx, body=body)
            log.info(
                "index_created",
                index=self._chunk_idx,
            )
        except Exception as exc:
            raise IndexCreationError(str(exc)) from exc

    def _ensure_rrf_pipeline(self) -> None:
        pipeline = build_rrf_pipeline(self._cfg.rrf_pipeline)
        self._os.http.put(
            f"/_search/pipeline/{self._cfg.rrf_pipeline}",
            body=pipeline,
        )

    # -- search ---------------------------------------------------

    def execute_search(
        self,
        query: str,
        *,
        embedding: list[float] | None = None,
        size: int = 10,
        offset: int = 0,
        hybrid: bool = True,
        categories: list[str] | None = None,
        latest_only: bool = False,
        min_score: float | None = None,
    ) -> dict[str, Any]:
        """Run BM25 or hybrid search and return raw hits."""
        builder = (
            DslBuilder()
            .text(query)
            .paginate(size, offset)
            .filter_categories(categories)
            .only_latest(latest_only)
            .threshold(min_score)
        )
        params: dict[str, Any] = {}

        if hybrid and embedding is not None:
            builder.vector(embedding)
            body = builder.build_hybrid(k=size)
            params["search_pipeline"] = self._cfg.rrf_pipeline
        else:
            body = builder.build_bm25()

        try:
            resp = self._os.search(
                index=self._chunk_idx,
                body=body,
                params=params,
            )
        except Exception as exc:
            log.error("search_failed", query=query, err=str(exc))
            raise SearchEngineError(str(exc)) from exc

        hits = resp.get("hits", {})
        log.info(
            "search_executed",
            query=query[:80],
            mode="hybrid" if hybrid else "bm25",
            total=hits.get("total", {}).get("value", 0),
        )
        return hits

    # -- single-doc ingest ----------------------------------------

    def index_chunk(self, doc_id: str, body: dict[str, Any]) -> None:
        """Index a single chunk document."""
        self._os.index(
            index=self._chunk_idx,
            id=doc_id,
            body=body,
        )

    def bulk_index(self, actions: list[dict[str, Any]]) -> int:
        """Bulk-index a list of chunk documents.

        Returns the number of successfully indexed docs.
        """
        if not actions:
            return 0
        from opensearchpy.helpers import bulk

        ok, errors = bulk(self._os, actions, index=self._chunk_idx)
        if errors:
            log.warning(
                "bulk_index_errors",
                count=len(errors),
            )
        log.info("bulk_indexed", count=ok)
        return ok

    # -- health ---------------------------------------------------

    def check_health(self) -> dict[str, Any]:
        """Return cluster health + document count."""
        try:
            health = self._os.cluster.health()
            stats = self._os.indices.stats(index=self._chunk_idx)
            doc_count = (
                stats.get("_all", {})
                .get("primaries", {})
                .get("docs", {})
                .get("count", 0)
            )
            return {
                "status": "healthy",
                "cluster": health.get("status", "unknown"),
                "documents": doc_count,
            }
        except Exception as exc:
            return {
                "status": "unhealthy",
                "error": str(exc),
            }

    @property
    def chunk_index_name(self) -> str:
        return self._chunk_idx


def create_search_engine(cfg: SearchCfg) -> SearchEngine:
    """Factory: build a ``SearchEngine`` from config."""
    os_client = OpenSearch(
        hosts=[cfg.host],
        use_ssl=False,
        verify_certs=False,
        timeout=30,
    )
    return SearchEngine(os_client, cfg)
