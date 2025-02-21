"""POST /api/v1/feedback — attach user scores to traces."""

from __future__ import annotations

import structlog
from fastapi import APIRouter, HTTPException

from sentinel.api.deps import TracerDep
from sentinel.api.schemas import (
    FeedbackBody,
    FeedbackPayload,
)

log = structlog.get_logger(__name__)
router = APIRouter(tags=["feedback"])


@router.post(
    "/feedback",
    response_model=FeedbackPayload,
)
async def submit_feedback(
    body: FeedbackBody,
    tracer: TracerDep,
) -> FeedbackPayload:
    """Record user feedback for a previous trace."""
    if tracer is None:
        raise HTTPException(
            status_code=503,
            detail="Tracing is not enabled",
        )

    ok = tracer.record_feedback(
        trace_id=body.trace_id,
        score=body.score,
        comment=body.comment,
    )
    if not ok:
        log.warning(
            "feedback_rejected",
            trace_id=body.trace_id,
        )
    return FeedbackPayload(success=ok)
