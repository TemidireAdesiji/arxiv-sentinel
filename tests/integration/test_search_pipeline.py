"""Integration: index a document, then retrieve it.

Requires OpenSearch running on localhost:9200.
"""

from __future__ import annotations

import pytest

from sentinel.search.client import SearchEngine
from sentinel.settings import SearchCfg

pytestmark = pytest.mark.integration


@pytest.fixture()
def search_cfg() -> SearchCfg:
    return SearchCfg(
        host="http://localhost:9200",
        index="test-sentinel",
        chunk_suffix="-chunks",
        vector_dim=3,
    )


@pytest.fixture()
def engine(search_cfg) -> SearchEngine:
    from opensearchpy import OpenSearch

    os_client = OpenSearch(
        hosts=[search_cfg.host],
        use_ssl=False,
        verify_certs=False,
        timeout=10,
    )
    eng = SearchEngine(os_client, search_cfg)
    yield eng
    idx = eng.chunk_index_name
    try:
        os_client.indices.delete(index=idx)
    except Exception:
        pass


class TestRoundTrip:
    def test_index_and_search(self, engine):
        engine.ensure_index()
        engine.index_chunk(
            "doc1",
            {
                "arxiv_id": "9999.00001",
                "title": "Unique Test Paper",
                "chunk_body": "Unique sentinel text",
                "embedding": [0.1, 0.2, 0.3],
            },
        )
        import time

        time.sleep(2)

        hits = engine.execute_search(
            "sentinel text",
            size=5,
            hybrid=False,
        )
        raw = hits.get("hits", [])
        assert len(raw) > 0
        assert raw[0]["_source"]["arxiv_id"] == "9999.00001"
