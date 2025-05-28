"""POST /api/v1/ask-agentic — multi-step RAG with reasoning."""

from __future__ import annotations

import structlog
from fastapi import APIRouter, HTTPException

from sentinel.api.deps import AgentDep
from sentinel.api.schemas import (
    AgenticPayload,
    QuestionBody,
)

log = structlog.get_logger(__name__)
router = APIRouter(tags=["agentic"])


@router.post(
    "/ask-agentic",
    response_model=AgenticPayload,
)
async def agentic_answer(
    body: QuestionBody,
    agent: AgentDep,
) -> AgenticPayload:
    """Run the full agentic pipeline and return reasoning."""
    if agent is None:
        raise HTTPException(
            status_code=503,
            detail="Agent service is not available",
        )

    result = await agent.process_query(body.query)

    return AgenticPayload(
        query=result.query,
        answer=result.answer,
        sources=result.sources,
        reasoning_steps=result.reasoning_steps,
        retrieval_attempts=result.retrieval_attempts,
        trace_id=result.trace_id,
    )
