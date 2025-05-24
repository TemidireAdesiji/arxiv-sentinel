"""Individual node functions for the agentic pipeline.

Each function has the signature::

    async def node(state: PipelineState, ctx: NodeContext)
        -> PipelineState

Nodes mutate ``state`` in place and return it.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import structlog

from sentinel.agent.state import PipelineState
from sentinel.llm.prompts import (
    GRADING_TEMPLATE,
    GUARDRAIL_TEMPLATE,
    REWRITE_TEMPLATE,
    build_rag_prompt,
)

log = structlog.get_logger(__name__)

# ── Context shared across nodes ─────────────────────


@dataclass
class NodeContext:
    """Immutable bag of dependencies injected into nodes."""

    search: Any  # SearchEngine
    embedder: Any  # EmbeddingProvider
    llm: Any  # InferenceClient
    model_name: str = "llama3.2:1b"
    temperature: float = 0.0
    guardrail_threshold: int = 60
    max_attempts: int = 2
    use_hybrid: bool = True
    top_k: int = 5


# ── Node implementations ────────────────────────────


async def check_guardrail(
    state: PipelineState,
    ctx: NodeContext,
) -> PipelineState:
    """Score the query for topical relevance (0-100)."""
    prompt = GUARDRAIL_TEMPLATE.format(
        query=state.query,
    )
    raw = await ctx.llm.generate(prompt, temperature=0.0)
    score = _parse_int(raw, fallback=100)
    state.guardrail_score = score
    state.reasoning.append(f"Guardrail score: {score}/100")
    log.info(
        "guardrail_checked",
        query=state.query[:60],
        score=score,
    )
    return state


async def reject_query(
    state: PipelineState,
    ctx: NodeContext,
) -> PipelineState:
    """Produce a polite rejection for off-topic queries."""
    state.answer = (
        "This question appears to be outside the scope "
        "of arXiv CS/AI research papers. Please ask "
        "about computer-science or AI research topics."
    )
    state.reasoning.append("Query rejected as off-topic")
    return state


async def fetch_relevant_docs(
    state: PipelineState,
    ctx: NodeContext,
) -> PipelineState:
    """Retrieve documents from the search engine."""
    state.attempt_count += 1
    query = state.effective_query
    state.reasoning.append(
        f"Retrieval attempt {state.attempt_count}: {query!r}"
    )

    embedding = None
    if ctx.use_hybrid:
        embedding = await ctx.embedder.embed_query(query)

    hits = ctx.search.execute_search(
        query,
        embedding=embedding,
        size=ctx.top_k,
        hybrid=ctx.use_hybrid,
    )
    raw_hits = hits.get("hits", [])
    state.documents = raw_hits
    state.sources = _extract_sources(raw_hits)
    log.info(
        "docs_retrieved",
        count=len(raw_hits),
        attempt=state.attempt_count,
    )
    return state


async def assess_relevance(
    state: PipelineState,
    ctx: NodeContext,
) -> PipelineState:
    """Grade each retrieved document for relevance."""
    if not state.documents:
        state.route = "refine"
        state.reasoning.append("No documents retrieved — will refine query")
        return state

    relevant: list[dict[str, Any]] = []
    for doc in state.documents:
        src = doc.get("_source", {})
        text = src.get("chunk_body", src.get("abstract", ""))
        prompt = GRADING_TEMPLATE.format(
            question=state.effective_query,
            document=text[:500],
        )
        raw = await ctx.llm.generate(prompt, temperature=0.0)
        if _parse_relevant(raw):
            relevant.append(doc)

    state.documents = relevant
    if relevant:
        state.route = "generate"
        state.reasoning.append(f"{len(relevant)} relevant document(s) found")
    else:
        state.route = "refine"
        state.reasoning.append("No documents deemed relevant")
    return state


async def refine_query(
    state: PipelineState,
    ctx: NodeContext,
) -> PipelineState:
    """Rewrite the query for better retrieval."""
    prompt = REWRITE_TEMPLATE.format(
        query=state.effective_query,
    )
    rewritten = await ctx.llm.generate(prompt, temperature=0.3)
    state.refined_query = rewritten.strip()
    state.reasoning.append(f"Query rewritten to: {state.refined_query!r}")
    return state


async def compose_response(
    state: PipelineState,
    ctx: NodeContext,
) -> PipelineState:
    """Generate the final answer from retrieved context."""
    chunks = [
        doc.get("_source", {}).get("chunk_body", "")
        for doc in state.documents
        if doc.get("_source", {}).get("chunk_body")
    ]
    if not chunks:
        state.answer = (
            "I could not find relevant information "
            "in the indexed papers to answer this "
            "question."
        )
        state.reasoning.append("No usable context — returned fallback")
        return state

    prompt = build_rag_prompt(state.query, chunks)
    state.answer = await ctx.llm.generate(prompt, temperature=ctx.temperature)
    state.reasoning.append(f"Answer generated from {len(chunks)} chunk(s)")
    return state


# ── Router functions ─────────────────────────────────


def route_after_guardrail(
    state: PipelineState,
) -> str:
    """Decide whether to proceed or reject."""

    if state.guardrail_score < 60:
        return "reject"
    return "retrieve"


def route_after_grading(
    state: PipelineState,
) -> str:
    """Decide: generate, refine, or give up."""

    if state.route == "generate":
        return "generate"
    if state.attempt_count >= 2:
        return "generate"
    return "rewrite"


# ── Helpers ──────────────────────────────────────────


def _parse_int(text: str, *, fallback: int) -> int:
    try:
        data = json.loads(text.strip().strip("`").strip())
        return int(data.get("score", fallback))
    except (json.JSONDecodeError, ValueError, TypeError):
        for word in text.split():
            cleaned = word.strip(".,;:!?\"'")
            if cleaned.isdigit():
                return int(cleaned)
        return fallback


def _parse_relevant(text: str) -> bool:
    try:
        data = json.loads(text.strip().strip("`").strip())
        return str(data.get("relevant", "no")).lower() == "yes"
    except (json.JSONDecodeError, ValueError, TypeError):
        return "yes" in text.lower()


def _extract_sources(
    hits: list[dict[str, Any]],
) -> list[str]:
    seen: set[str] = set()
    sources: list[str] = []
    for h in hits:
        aid = h.get("_source", {}).get("arxiv_id", "")
        if aid and aid not in seen:
            seen.add(aid)
            sources.append(f"https://arxiv.org/abs/{aid}")
    return sources
