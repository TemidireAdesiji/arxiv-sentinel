"""Tests for POST /api/v1/search."""

from __future__ import annotations


class TestSearchEndpoint:
    async def test_returns_200(self, client):
        resp = await client.post(
            "/api/v1/search",
            json={"query": "transformers"},
        )
        assert resp.status_code == 200

    async def test_response_has_hits(self, client):
        data = (
            await client.post(
                "/api/v1/search",
                json={"query": "llm"},
            )
        ).json()
        assert "hits" in data
        assert len(data["hits"]) > 0

    async def test_hit_contains_arxiv_id(self, client):
        data = (
            await client.post(
                "/api/v1/search",
                json={"query": "rag"},
            )
        ).json()
        assert data["hits"][0]["arxiv_id"]

    async def test_empty_query_rejected(self, client):
        resp = await client.post("/api/v1/search", json={"query": ""})
        assert resp.status_code == 422

    async def test_mode_reflects_hybrid_flag(self, client):
        data = (
            await client.post(
                "/api/v1/search",
                json={
                    "query": "q",
                    "hybrid": False,
                },
            )
        ).json()
        assert data["mode"] == "bm25"
