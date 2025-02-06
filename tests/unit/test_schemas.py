"""Tests for sentinel.api.schemas — request/response validation."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from sentinel.api.schemas import (
    FeedbackBody,
    QuestionBody,
    SearchBody,
)


class TestSearchBodyValidation:
    def test_minimal_valid(self):
        body = SearchBody(query="test")
        assert body.size == 10
        assert body.hybrid is True

    def test_empty_query_rejected(self):
        with pytest.raises(ValidationError):
            SearchBody(query="")

    def test_size_bounds(self):
        with pytest.raises(ValidationError):
            SearchBody(query="q", size=0)
        with pytest.raises(ValidationError):
            SearchBody(query="q", size=200)

    def test_categories_optional(self):
        body = SearchBody(query="q", categories=["cs.AI"])
        assert body.categories == ["cs.AI"]


class TestQuestionBodyValidation:
    def test_defaults(self):
        body = QuestionBody(query="q")
        assert body.top_k == 3
        assert body.hybrid is True
        assert body.model == "llama3.2:1b"

    def test_top_k_bounds(self):
        with pytest.raises(ValidationError):
            QuestionBody(query="q", top_k=0)
        with pytest.raises(ValidationError):
            QuestionBody(query="q", top_k=20)

    def test_query_too_long(self):
        with pytest.raises(ValidationError):
            QuestionBody(query="x" * 1001)


class TestFeedbackBodyValidation:
    def test_valid(self):
        body = FeedbackBody(trace_id="abc", score=0.8)
        assert body.comment == ""

    def test_score_bounds(self):
        with pytest.raises(ValidationError):
            FeedbackBody(trace_id="x", score=-0.1)
        with pytest.raises(ValidationError):
            FeedbackBody(trace_id="x", score=1.1)

    def test_empty_trace_id_rejected(self):
        with pytest.raises(ValidationError):
            FeedbackBody(trace_id="", score=0.5)
