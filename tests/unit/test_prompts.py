"""Tests for sentinel.llm.prompts — template correctness."""

from __future__ import annotations

from sentinel.llm.prompts import (
    GRADING_TEMPLATE,
    GUARDRAIL_TEMPLATE,
    REWRITE_TEMPLATE,
    build_rag_prompt,
)


class TestBuildRagPrompt:
    def test_includes_question(self):
        result = build_rag_prompt("What is RAG?", ["chunk1"])
        assert "What is RAG?" in result

    def test_includes_numbered_chunks(self):
        result = build_rag_prompt("q", ["alpha", "beta"])
        assert "[1] alpha" in result
        assert "[2] beta" in result

    def test_empty_chunks_still_has_question(self):
        result = build_rag_prompt("q", [])
        assert "q" in result


class TestTemplateFormatting:
    def test_guardrail_accepts_query(self):
        out = GUARDRAIL_TEMPLATE.format(query="test")
        assert "test" in out

    def test_grading_accepts_both_fields(self):
        out = GRADING_TEMPLATE.format(question="q", document="d")
        assert "q" in out
        assert "d" in out

    def test_rewrite_accepts_query(self):
        out = REWRITE_TEMPLATE.format(query="old")
        assert "old" in out
