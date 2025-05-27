"""Tests for POST /api/v1/ask-agentic."""

from __future__ import annotations


class TestAgenticEndpoint:
    async def test_returns_200(self, client):
        resp = await client.post(
            "/api/v1/ask-agentic",
            json={"query": "Latest in NLP?"},
        )
        assert resp.status_code == 200

    async def test_response_has_reasoning(self, client):
        data = (
            await client.post(
                "/api/v1/ask-agentic",
                json={"query": "q"},
            )
        ).json()
        assert "reasoning_steps" in data
        assert len(data["reasoning_steps"]) > 0

    async def test_response_has_trace_id(self, client):
        data = (
            await client.post(
                "/api/v1/ask-agentic",
                json={"query": "q"},
            )
        ).json()
        assert data["trace_id"] is not None

    async def test_retrieval_attempts_tracked(self, client):
        data = (
            await client.post(
                "/api/v1/ask-agentic",
                json={"query": "q"},
            )
        ).json()
        assert data["retrieval_attempts"] >= 0
