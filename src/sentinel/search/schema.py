"""OpenSearch index mappings and RRF pipeline definition."""

from __future__ import annotations

from typing import Any


def build_chunk_mapping(
    vector_dim: int = 1024,
    space: str = "cosinesimil",
) -> dict[str, Any]:
    """Return the index body for the hybrid chunk index."""
    return {
        "settings": {
            "index": {
                "knn": True,
                "knn.algo_param.ef_search": 100,
            },
        },
        "mappings": {
            "properties": {
                "arxiv_id": {
                    "type": "keyword",
                },
                "paper_id": {
                    "type": "keyword",
                },
                "title": {
                    "type": "text",
                    "analyzer": "standard",
                },
                "authors": {
                    "type": "text",
                },
                "abstract": {
                    "type": "text",
                    "analyzer": "standard",
                },
                "categories": {
                    "type": "keyword",
                },
                "published_at": {
                    "type": "date",
                },
                "chunk_index": {
                    "type": "integer",
                },
                "chunk_body": {
                    "type": "text",
                    "analyzer": "standard",
                },
                "section_title": {
                    "type": "keyword",
                },
                "word_count": {
                    "type": "integer",
                },
                "embedding": {
                    "type": "knn_vector",
                    "dimension": vector_dim,
                    "method": {
                        "name": "hnsw",
                        "space_type": space,
                        "engine": "nmslib",
                        "parameters": {
                            "ef_construction": 128,
                            "m": 24,
                        },
                    },
                },
            },
        },
    }


def build_rrf_pipeline(
    name: str = "hybrid-rrf-pipeline",
) -> dict[str, Any]:
    """Return the search-pipeline body for RRF."""
    return {
        "description": "RRF combination of BM25 + KNN",
        "phase_results_processors": [
            {
                "normalization-processor": {
                    "normalization": {
                        "technique": "min_max",
                    },
                    "combination": {
                        "technique": "arithmetic_mean",
                        "parameters": {
                            "weights": [0.3, 0.7],
                        },
                    },
                },
            },
        ],
    }
