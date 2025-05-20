"""Tests for POST /api/v1/ask."""

from __future__ import annotations


class TestAskEndpoint:
    async def test_returns_200(self, client):
        resp = await client.post(
            "/api/v1/ask",
            json={"query": "What is RAG?"},
        )
        assert resp.status_code == 200

    async def test_response_has_answer(self, client):
        data = (
            await client.post(
                "/api/v1/ask",
                json={"query": "Explain LLM"},
            )
        ).json()
        assert data["answer"]
        assert data["query"] == "Explain LLM"

    async def test_sources_populated(self, client):
        data = (
            await client.post(
                "/api/v1/ask",
                json={"query": "q"},
            )
        ).json()
        assert isinstance(data["sources"], list)

    async def test_chunks_used_positive(self, client):
        data = (
            await client.post(
                "/api/v1/ask",
                json={"query": "q"},
            )
        ).json()
        assert data["chunks_used"] >= 0

    async def test_empty_query_rejected(self, client):
        resp = await client.post("/api/v1/ask", json={"query": ""})
        assert resp.status_code == 422

    async def test_custom_top_k(self, client):
        resp = await client.post(
            "/api/v1/ask",
            json={"query": "q", "top_k": 5},
        )
        assert resp.status_code == 200
