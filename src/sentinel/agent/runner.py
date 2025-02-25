"""Top-level orchestrator that wires the agent graph."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from sentinel.agent.graph import END, WorkflowGraph
from sentinel.agent.nodes import (
    NodeContext,
    assess_relevance,
    check_guardrail,
    compose_response,
    fetch_relevant_docs,
    refine_query,
    reject_query,
    route_after_grading,
    route_after_guardrail,
)
from sentinel.agent.state import (
    AgenticResult,
    PipelineState,
)

if TYPE_CHECKING:
    from sentinel.embeddings.jina import (
        EmbeddingProvider,
    )
    from sentinel.llm.client import InferenceClient
    from sentinel.search.client import SearchEngine
    from sentinel.tracing.langfuse import TraceRecorder

log = structlog.get_logger(__name__)


class AgentOrchestrator:
    """Build and run the agentic RAG workflow."""

    def __init__(
        self,
        search: SearchEngine,
        embedder: EmbeddingProvider,
        llm: InferenceClient,
        tracer: TraceRecorder | None = None,
        *,
        model_name: str = "llama3.2:1b",
        guardrail_threshold: int = 60,
        max_attempts: int = 2,
        use_hybrid: bool = True,
        top_k: int = 5,
    ) -> None:
        self._tracer = tracer
        self._ctx = NodeContext(
            search=search,
            embedder=embedder,
            llm=llm,
            model_name=model_name,
            guardrail_threshold=guardrail_threshold,
            max_attempts=max_attempts,
            use_hybrid=use_hybrid,
            top_k=top_k,
        )
        self._graph = self._build_graph()

    async def process_query(
        self,
        query: str,
    ) -> AgenticResult:
        """Run the full agentic pipeline on *query*."""
        trace = None
        trace_id = None
        if self._tracer:
            trace = self._tracer.begin_trace(
                "agentic_ask",
                metadata={"query": query},
            )
            trace_id = trace.trace_id

        state = PipelineState(query=query)
        try:
            state = await self._graph.execute("guardrail", state, self._ctx)
        except Exception:
            log.exception(
                "agent_pipeline_failed",
                query=query[:80],
            )
            state.answer = (
                "An internal error occurred while processing your question."
            )
            state.reasoning.append("Pipeline error")

        if self._tracer and trace:
            self._tracer.flush()

        return AgenticResult(
            query=query,
            answer=state.answer,
            sources=state.sources,
            reasoning_steps=state.reasoning,
            retrieval_attempts=state.attempt_count,
            trace_id=trace_id,
        )

    # -- graph construction ---------------------------------------

    @staticmethod
    def _build_graph() -> WorkflowGraph:
        g = WorkflowGraph()

        g.add_node("guardrail", check_guardrail)
        g.add_node("reject", reject_query)
        g.add_node("retrieve", fetch_relevant_docs)
        g.add_node("grade", assess_relevance)
        g.add_node("rewrite", refine_query)
        g.add_node("generate", compose_response)

        g.add_conditional_edge("guardrail", route_after_guardrail)
        g.add_edge("reject", END)
        g.add_edge("retrieve", "grade")
        g.add_conditional_edge("grade", route_after_grading)
        g.add_edge("rewrite", "retrieve")
        g.add_edge("generate", END)

        return g


def create_agent_orchestrator(
    search: SearchEngine,
    embedder: EmbeddingProvider,
    llm: InferenceClient,
    tracer: TraceRecorder | None = None,
) -> AgentOrchestrator:
    """Factory: build an ``AgentOrchestrator``."""
    return AgentOrchestrator(
        search=search,
        embedder=embedder,
        llm=llm,
        tracer=tracer,
    )
