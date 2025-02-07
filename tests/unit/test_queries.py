"""Tests for sentinel.search.queries — DSL construction."""

from __future__ import annotations

import pytest

from sentinel.search.queries import DslBuilder


class TestBm25QueryBuild:
    def test_basic_multi_match(self):
        body = DslBuilder().text("transformers").paginate(5).build_bm25()
        assert body["size"] == 5
        must = body["query"]["bool"]["must"]
        assert must[0]["multi_match"]["query"] == ("transformers")

    def test_category_filter(self):
        body = (
            DslBuilder()
            .text("llm")
            .filter_categories(["cs.AI", "cs.CL"])
            .build_bm25()
        )
        filt = body["query"]["bool"]["filter"]
        assert filt[0]["terms"]["categories"] == [
            "cs.AI",
            "cs.CL",
        ]

    def test_latest_only_adds_date_range(self):
        body = DslBuilder().text("rag").only_latest().build_bm25()
        filt = body["query"]["bool"]["filter"]
        assert any("range" in f for f in filt)

    def test_min_score_propagated(self):
        body = DslBuilder().text("q").threshold(0.5).build_bm25()
        assert body["min_score"] == 0.5

    def test_highlight_present(self):
        body = DslBuilder().text("q").build_bm25()
        assert "chunk_body" in body["highlight"]["fields"]


class TestHybridQueryBuild:
    def test_requires_vector(self):
        with pytest.raises(ValueError):
            DslBuilder().text("q").build_hybrid()

    def test_hybrid_contains_knn(self):
        body = DslBuilder().text("q").vector([0.1] * 10).build_hybrid()
        queries = body["query"]["hybrid"]["queries"]
        assert len(queries) == 2
        assert "knn" in queries[1]

    def test_hybrid_size_and_offset(self):
        body = (
            DslBuilder()
            .text("q")
            .vector([0.1] * 10)
            .paginate(7, 3)
            .build_hybrid()
        )
        assert body["size"] == 7
        assert body["from"] == 3
