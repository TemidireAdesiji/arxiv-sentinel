"""POST /api/v1/ask — standard RAG question-answering.

Also serves ``POST /api/v1/stream`` with SSE streaming.
"""

from __future__ import annotations

import json
from typing import Any

import structlog
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from sentinel.api.deps import (
    CacheDep,
    EmbedDep,
    LlmDep,
    SearchDep,
    TracerDep,
)
from sentinel.api.schemas import (
    AnswerPayload,
    QuestionBody,
)
from sentinel.llm.prompts import build_rag_prompt

log = structlog.get_logger(__name__)
router = APIRouter(tags=["ask"])
stream_router = APIRouter(tags=["ask"])


@router.post(
    "/ask",
    response_model=AnswerPayload,
)
async def answer_question(
    body: QuestionBody,
    search: SearchDep,
    embedder: EmbedDep,
    llm: LlmDep,
    tracer: TracerDep,
    cache: CacheDep,
) -> AnswerPayload:
    """Answer a research question using retrieved context."""
    cache_params = {
        "query": body.query,
        "model": body.model,
        "top_k": body.top_k,
        "hybrid": body.hybrid,
        "categories": body.categories,
    }
    if cache:
        hit = cache.lookup(**cache_params)
        if hit:
            log.info("cache_hit", query=body.query[:60])
            return AnswerPayload(**hit)

    trace = None
    trace_id = None
    if tracer:
        trace = tracer.begin_trace("ask", metadata={"query": body.query})
        trace_id = trace.trace_id

    embedding = None
    if body.hybrid:
        embedding = await embedder.embed_query(body.query)

    raw_hits = search.execute_search(
        body.query,
        embedding=embedding,
        size=body.top_k,
        hybrid=body.hybrid,
        categories=body.categories,
    )
    docs = raw_hits.get("hits", [])
    chunks = _collect_chunks(docs)
    sources = _collect_sources(docs)

    prompt = build_rag_prompt(body.query, chunks)
    answer = await llm.generate(prompt)

    payload = AnswerPayload(
        query=body.query,
        answer=answer,
        sources=sources,
        chunks_used=len(chunks),
        mode="hybrid" if body.hybrid else "bm25",
        trace_id=trace_id,
    )

    if cache:
        cache.store(payload.model_dump(), **cache_params)

    if tracer and trace:
        tracer.flush()

    return payload


@stream_router.post("/stream")
async def stream_answer(
    body: QuestionBody,
    search: SearchDep,
    embedder: EmbedDep,
    llm: LlmDep,
) -> StreamingResponse:
    """Stream a RAG answer as server-sent events."""

    async def _generate():
        embedding = None
        if body.hybrid:
            embedding = await embedder.embed_query(body.query)
        raw_hits = search.execute_search(
            body.query,
            embedding=embedding,
            size=body.top_k,
            hybrid=body.hybrid,
            categories=body.categories,
        )
        docs = raw_hits.get("hits", [])
        chunks = _collect_chunks(docs)
        sources = _collect_sources(docs)

        meta = {
            "sources": sources,
            "chunks_used": len(chunks),
            "mode": ("hybrid" if body.hybrid else "bm25"),
        }
        yield _sse("metadata", json.dumps(meta))

        prompt = build_rag_prompt(body.query, chunks)
        async for token in llm.generate_stream(prompt):
            yield _sse("token", token)

        yield _sse("done", "")

    return StreamingResponse(
        _generate(),
        media_type="text/event-stream",
    )


# ── helpers ──────────────────────────────────────────


def _collect_chunks(
    docs: list[dict[str, Any]],
) -> list[str]:
    return [
        d.get("_source", {}).get("chunk_body", "")
        for d in docs
        if d.get("_source", {}).get("chunk_body")
    ]


def _collect_sources(
    docs: list[dict[str, Any]],
) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for d in docs:
        aid = d.get("_source", {}).get("arxiv_id", "")
        if aid and aid not in seen:
            seen.add(aid)
            out.append(f"https://arxiv.org/abs/{aid}")
    return out


def _sse(event: str, data: str) -> str:
    return f"event: {event}\ndata: {data}\n\n"
