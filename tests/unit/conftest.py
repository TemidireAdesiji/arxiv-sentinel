"""Unit-test fixtures — mocks for every external service."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from sentinel.agent.nodes import NodeContext
from sentinel.agent.state import PipelineState


@pytest.fixture()
def mock_search() -> MagicMock:
    """Fake SearchEngine."""
    m = MagicMock()
    m.execute_search.return_value = {
        "hits": [
            {
                "_source": {
                    "arxiv_id": "2401.00001",
                    "title": "Test Paper",
                    "authors": ["Alice"],
                    "abstract": "An abstract.",
                    "chunk_body": "Some content.",
                    "categories": ["cs.AI"],
                },
                "_score": 0.95,
            },
        ],
        "total": {"value": 1},
    }
    m.check_health.return_value = {
        "status": "healthy",
        "documents": 42,
    }
    return m


@pytest.fixture()
def mock_embedder() -> AsyncMock:
    """Fake EmbeddingProvider."""
    m = AsyncMock()
    m.embed_query.return_value = [0.1] * 1024
    m.embed_passages.return_value = [[0.1] * 1024]
    return m


@pytest.fixture()
def mock_llm() -> AsyncMock:
    """Fake InferenceClient."""
    m = AsyncMock()
    m.generate.return_value = "Generated answer."
    m.check_health.return_value = {
        "status": "healthy",
        "version": "0.1.0",
    }
    return m


@pytest.fixture()
def mock_tracer() -> MagicMock:
    """Fake TraceRecorder."""
    m = MagicMock()
    trace = MagicMock()
    trace.trace_id = "trace-abc"
    m.begin_trace.return_value = trace
    m.record_feedback.return_value = True
    return m


@pytest.fixture()
def mock_cache() -> MagicMock:
    """Fake CacheStore."""
    m = MagicMock()
    m.lookup.return_value = None
    m.is_available.return_value = True
    return m


@pytest.fixture()
def sample_node_ctx(mock_search, mock_embedder, mock_llm) -> NodeContext:
    """NodeContext wired to all mocks."""
    return NodeContext(
        search=mock_search,
        embedder=mock_embedder,
        llm=mock_llm,
    )


@pytest.fixture()
def blank_state() -> PipelineState:
    """Empty pipeline state for a test query."""
    return PipelineState(query="test query")
