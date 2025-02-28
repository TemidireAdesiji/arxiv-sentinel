"""Tests for sentinel.agent.nodes — individual node logic."""

from __future__ import annotations

from sentinel.agent.nodes import (
    _parse_int,
    _parse_relevant,
    assess_relevance,
    check_guardrail,
    compose_response,
    fetch_relevant_docs,
    refine_query,
    reject_query,
    route_after_grading,
    route_after_guardrail,
)
from sentinel.agent.state import PipelineState


class TestCheckGuardrail:
    async def test_high_score_passes(self, sample_node_ctx, blank_state):
        sample_node_ctx.llm.generate.return_value = '{"score": 90}'
        state = await check_guardrail(blank_state, sample_node_ctx)
        assert state.guardrail_score == 90
        assert len(state.reasoning) == 1

    async def test_low_score_recorded(self, sample_node_ctx, blank_state):
        sample_node_ctx.llm.generate.return_value = '{"score": 20}'
        state = await check_guardrail(blank_state, sample_node_ctx)
        assert state.guardrail_score == 20


class TestRejectQuery:
    async def test_produces_rejection_message(
        self, sample_node_ctx, blank_state
    ):
        state = await reject_query(blank_state, sample_node_ctx)
        assert "outside the scope" in state.answer


class TestFetchRelevantDocs:
    async def test_increments_attempt(self, sample_node_ctx, blank_state):
        state = await fetch_relevant_docs(blank_state, sample_node_ctx)
        assert state.attempt_count == 1
        assert len(state.documents) > 0

    async def test_populates_sources(self, sample_node_ctx, blank_state):
        state = await fetch_relevant_docs(blank_state, sample_node_ctx)
        assert any("arxiv.org" in s for s in state.sources)


class TestAssessRelevance:
    async def test_relevant_doc_kept(self, sample_node_ctx):
        sample_node_ctx.llm.generate.return_value = '{"relevant": "yes"}'
        state = PipelineState(
            query="q",
            documents=[{"_source": {"chunk_body": "some text"}}],
        )
        state = await assess_relevance(state, sample_node_ctx)
        assert state.route == "generate"
        assert len(state.documents) == 1

    async def test_irrelevant_doc_removed(self, sample_node_ctx):
        sample_node_ctx.llm.generate.return_value = '{"relevant": "no"}'
        state = PipelineState(
            query="q",
            documents=[{"_source": {"chunk_body": "text"}}],
        )
        state = await assess_relevance(state, sample_node_ctx)
        assert state.route == "refine"

    async def test_empty_docs_triggers_refine(self, sample_node_ctx):
        state = PipelineState(query="q", documents=[])
        state = await assess_relevance(state, sample_node_ctx)
        assert state.route == "refine"


class TestRefineQuery:
    async def test_sets_refined_query(self, sample_node_ctx, blank_state):
        sample_node_ctx.llm.generate.return_value = "improved query"
        state = await refine_query(blank_state, sample_node_ctx)
        assert state.refined_query == "improved query"


class TestComposeResponse:
    async def test_answer_from_chunks(self, sample_node_ctx):
        state = PipelineState(
            query="q",
            documents=[{"_source": {"chunk_body": "info"}}],
        )
        state = await compose_response(state, sample_node_ctx)
        assert state.answer == "Generated answer."

    async def test_fallback_when_no_chunks(self, sample_node_ctx):
        state = PipelineState(query="q", documents=[])
        state = await compose_response(state, sample_node_ctx)
        assert "could not find" in state.answer.lower()


class TestRouters:
    def test_guardrail_rejects_low_score(self):
        state = PipelineState(query="q", guardrail_score=30)
        assert route_after_guardrail(state) == "reject"

    def test_guardrail_proceeds_high_score(self):
        state = PipelineState(query="q", guardrail_score=80)
        assert route_after_guardrail(state) == "retrieve"

    def test_grading_generate_when_relevant(self):
        state = PipelineState(query="q", route="generate")
        assert route_after_grading(state) == "generate"

    def test_grading_rewrite_when_not_relevant(self):
        state = PipelineState(
            query="q",
            route="refine",
            attempt_count=1,
        )
        assert route_after_grading(state) == "rewrite"

    def test_grading_give_up_after_max_attempts(self):
        state = PipelineState(
            query="q",
            route="refine",
            attempt_count=2,
        )
        assert route_after_grading(state) == "generate"


class TestParsers:
    def test_parse_int_from_json(self):
        assert _parse_int('{"score": 75}', fallback=0) == 75

    def test_parse_int_fallback(self):
        assert _parse_int("garbage", fallback=50) == 50

    def test_parse_int_from_plain_number(self):
        assert _parse_int("Score: 82", fallback=0) == 82

    def test_parse_relevant_yes(self):
        assert _parse_relevant('{"relevant": "yes"}')

    def test_parse_relevant_no(self):
        assert not _parse_relevant('{"relevant": "no"}')

    def test_parse_relevant_fuzzy(self):
        assert _parse_relevant("Yes, it is relevant.")
