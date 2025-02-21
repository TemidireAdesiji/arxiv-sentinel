"""API test fixtures — async HTTP client with mocked services."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient

from sentinel.app import build_application


@pytest.fixture()
async def client():
    """Yield an async test client with all services mocked."""
    mock_db = MagicMock()
    mock_db.verify_connection.return_value = True

    mock_search = MagicMock()
    mock_search.ensure_index.return_value = None
    mock_search.check_health.return_value = {
        "status": "healthy",
        "documents": 10,
    }
    mock_search.execute_search.return_value = {
        "hits": [
            {
                "_source": {
                    "arxiv_id": "2401.00001",
                    "title": "Test",
                    "authors": ["A"],
                    "abstract": "Abs",
                    "chunk_body": "Content",
                    "categories": ["cs.AI"],
                },
                "_score": 0.9,
            },
        ],
        "total": {"value": 1},
    }

    mock_embedder = AsyncMock()
    mock_embedder.embed_query.return_value = [0.1] * 1024

    mock_llm = AsyncMock()
    mock_llm.generate.return_value = "Answer text."
    mock_llm.check_health.return_value = {
        "status": "healthy",
        "version": "0.1.0",
    }

    mock_tracer = MagicMock()
    trace = MagicMock()
    trace.trace_id = "trace-123"
    mock_tracer.begin_trace.return_value = trace
    mock_tracer.record_feedback.return_value = True

    mock_agent = AsyncMock()
    from sentinel.agent.state import AgenticResult

    mock_agent.process_query.return_value = AgenticResult(
        query="q",
        answer="Agentic answer",
        sources=["https://arxiv.org/abs/2401.00001"],
        reasoning_steps=["Step 1"],
        retrieval_attempts=1,
        trace_id="trace-456",
    )

    with (
        patch(
            "sentinel.lifespan.create_database_gateway",
            return_value=mock_db,
        ),
        patch(
            "sentinel.lifespan.create_search_engine",
            return_value=mock_search,
        ),
        patch(
            "sentinel.lifespan.create_embedding_provider",
            return_value=mock_embedder,
        ),
        patch(
            "sentinel.lifespan.create_inference_client",
            return_value=mock_llm,
        ),
        patch(
            "sentinel.lifespan.create_trace_recorder",
            return_value=mock_tracer,
        ),
        patch(
            "sentinel.lifespan.create_cache_store",
            return_value=None,
        ),
        patch(
            "sentinel.lifespan.create_arxiv_fetcher",
            return_value=MagicMock(),
        ),
        patch(
            "sentinel.lifespan.create_pdf_extractor",
            return_value=MagicMock(),
        ),
        patch(
            "sentinel.lifespan.create_agent_orchestrator",
            return_value=mock_agent,
        ),
        patch(
            "sentinel.db.models.Base.metadata.create_all",
        ),
    ):
        app = build_application()
        async with LifespanManager(app) as mgr:
            transport = ASGITransport(app=mgr.app)
            async with AsyncClient(
                transport=transport,
                base_url="http://test",
            ) as ac:
                yield ac
