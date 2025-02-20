"""Tests for GET /api/v1/health."""

from __future__ import annotations


class TestHealthEndpoint:
    async def test_returns_200(self, client):
        resp = await client.get("/api/v1/health")
        assert resp.status_code == 200

    async def test_contains_version(self, client):
        data = (await client.get("/api/v1/health")).json()
        assert "version" in data

    async def test_contains_services(self, client):
        data = (await client.get("/api/v1/health")).json()
        assert "database" in data["services"]
        assert "opensearch" in data["services"]
        assert "ollama" in data["services"]

    async def test_status_ok_when_healthy(self, client):
        data = (await client.get("/api/v1/health")).json()
        assert data["status"] == "ok"
