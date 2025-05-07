"""OpenSearch query DSL construction helpers."""

from __future__ import annotations

from typing import Any


class DslBuilder:
    """Fluent builder for OpenSearch query bodies.

    Produces either a plain BM25 ``multi_match`` or a hybrid
    query that pairs BM25 with a ``knn`` vector clause.
    """

    def __init__(self) -> None:
        self._query_text: str = ""
        self._embedding: list[float] | None = None
        self._size: int = 10
        self._offset: int = 0
        self._categories: list[str] | None = None
        self._latest_only: bool = False
        self._min_score: float | None = None
        self._sort_by_date: bool = False

    # -- setters (return self for chaining) -----------------------

    def text(self, q: str) -> DslBuilder:
        self._query_text = q
        return self

    def vector(self, emb: list[float]) -> DslBuilder:
        self._embedding = emb
        return self

    def paginate(self, size: int, offset: int = 0) -> DslBuilder:
        self._size = size
        self._offset = offset
        return self

    def filter_categories(self, cats: list[str] | None) -> DslBuilder:
        self._categories = cats
        return self

    def only_latest(self, flag: bool = True) -> DslBuilder:
        self._latest_only = flag
        return self

    def threshold(self, score: float | None) -> DslBuilder:
        self._min_score = score
        return self

    def order_by_date(self, flag: bool = True) -> DslBuilder:
        self._sort_by_date = flag
        return self

    # -- build ----------------------------------------------------

    def build_bm25(self) -> dict[str, Any]:
        """Construct a BM25-only query body."""
        body: dict[str, Any] = {
            "size": self._size,
            "from": self._offset,
            "query": self._bool_clause(),
        }
        if self._sort_by_date:
            body["sort"] = [{"published_at": {"order": "desc"}}]
        if self._min_score is not None:
            body["min_score"] = self._min_score
        body["highlight"] = self._highlight()
        return body

    def build_hybrid(self, *, k: int = 10) -> dict[str, Any]:
        """Construct a hybrid (BM25 + KNN) query body.

        Requires ``vector()`` to have been called first.
        """
        if self._embedding is None:
            raise ValueError("Call .vector(emb) before build_hybrid()")
        body: dict[str, Any] = {
            "size": self._size,
            "from": self._offset,
            "query": {
                "hybrid": {
                    "queries": [
                        self._bool_clause(),
                        {
                            "knn": {
                                "embedding": {
                                    "vector": self._embedding,
                                    "k": k,
                                },
                            },
                        },
                    ],
                },
            },
        }
        if self._min_score is not None:
            body["min_score"] = self._min_score
        body["highlight"] = self._highlight()
        return body

    # -- internal helpers -----------------------------------------

    def _bool_clause(self) -> dict[str, Any]:
        must = [
            {
                "multi_match": {
                    "query": self._query_text,
                    "fields": [
                        "title^3",
                        "abstract^2",
                        "chunk_body",
                    ],
                    "type": "best_fields",
                },
            },
        ]
        filters: list[dict[str, Any]] = []
        if self._categories:
            filters.append(
                {
                    "terms": {
                        "categories": self._categories,
                    },
                }
            )
        if self._latest_only:
            filters.append(
                {
                    "range": {
                        "published_at": {
                            "gte": "now-7d/d",
                        },
                    },
                }
            )
        clause: dict[str, Any] = {"bool": {"must": must}}
        if filters:
            clause["bool"]["filter"] = filters
        return clause

    @staticmethod
    def _highlight() -> dict[str, Any]:
        return {
            "fields": {
                "chunk_body": {
                    "fragment_size": 200,
                    "number_of_fragments": 2,
                },
                "abstract": {
                    "fragment_size": 200,
                    "number_of_fragments": 1,
                },
            },
        }
