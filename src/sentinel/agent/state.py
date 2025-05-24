"""Mutable pipeline state threaded through agent nodes."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class PipelineState:
    """Carries data between nodes during one request.

    Each node reads what it needs, mutates the relevant
    fields, and passes the state to the next node.
    """

    query: str
    refined_query: str = ""
    documents: list[dict[str, Any]] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)
    answer: str = ""
    reasoning: list[str] = field(default_factory=list)
    attempt_count: int = 0
    route: str = ""
    guardrail_score: int = 100

    @property
    def effective_query(self) -> str:
        """The query to use for the current retrieval."""
        return self.refined_query or self.query


@dataclass(frozen=True, slots=True)
class AgenticResult:
    """Immutable outcome returned to the caller."""

    query: str
    answer: str
    sources: list[str]
    reasoning_steps: list[str]
    retrieval_attempts: int
    trace_id: str | None = None
