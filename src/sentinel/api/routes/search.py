"""POST /api/v1/search — hybrid BM25 + vector search."""

from __future__ import annotations

from typing import Any

import structlog
from fastapi import APIRouter

from sentinel.api.deps import EmbedDep, SearchDep
from sentinel.api.schemas import (
    HitItem,
    SearchBody,
    SearchPayload,
)

log = structlog.get_logger(__name__)
router = APIRouter(tags=["search"])


@router.post(
    "/search",
    response_model=SearchPayload,
)
async def run_search(
    body: SearchBody,
    search: SearchDep,
    embedder: EmbedDep,
) -> SearchPayload:
    """Execute a hybrid or BM25 search over indexed chunks."""
    embedding = None
    if body.hybrid:
        embedding = await embedder.embed_query(body.query)

    raw = search.execute_search(
        body.query,
        embedding=embedding,
        size=body.size,
        offset=body.offset,
        hybrid=body.hybrid,
        categories=body.categories,
        latest_only=body.latest_only,
        min_score=body.min_score,
    )

    hits = [_to_hit(h) for h in raw.get("hits", [])]
    total = (
        raw.get("total", {}).get("value", 0)
        if isinstance(raw.get("total"), dict)
        else raw.get("total", 0)
    )

    return SearchPayload(
        query=body.query,
        mode="hybrid" if body.hybrid else "bm25",
        total=total,
        hits=hits,
    )


def _to_hit(raw: dict[str, Any]) -> HitItem:
    src = raw.get("_source", {})
    return HitItem(
        arxiv_id=src.get("arxiv_id", ""),
        title=src.get("title", ""),
        authors=src.get("authors", []),
        abstract=src.get("abstract", ""),
        score=raw.get("_score", 0.0),
        chunk_text=src.get("chunk_body", ""),
    )
