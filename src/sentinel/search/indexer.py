"""Content indexer: chunks papers, embeds, and bulk-indexes."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog

if TYPE_CHECKING:
    from sentinel.domain.chunk import TextFragment
    from sentinel.embeddings.jina import EmbeddingProvider
    from sentinel.search.client import SearchEngine

log = structlog.get_logger(__name__)

_BATCH = 100


class ContentIndexer:
    """Orchestrates chunking, embedding, and indexing."""

    def __init__(
        self,
        engine: SearchEngine,
        embedder: EmbeddingProvider,
    ) -> None:
        self._engine = engine
        self._embedder = embedder

    async def index_fragments(
        self,
        fragments: list[TextFragment],
        *,
        paper_meta: dict[str, Any],
    ) -> int:
        """Embed and bulk-index a list of text fragments.

        ``paper_meta`` is denormalised into every chunk
        document so search results carry full context.
        """
        if not fragments:
            return 0

        texts = [f.content for f in fragments]
        vectors = await self._embedder.embed_passages(texts)

        actions: list[dict[str, Any]] = []
        for frag, vec in zip(fragments, vectors):
            doc_id = f"{frag.arxiv_id}_chunk_{frag.index}"
            doc: dict[str, Any] = {
                "_id": doc_id,
                "arxiv_id": frag.arxiv_id,
                "paper_id": frag.paper_id,
                "title": paper_meta.get("title", ""),
                "authors": paper_meta.get("authors", []),
                "abstract": paper_meta.get("abstract", ""),
                "categories": paper_meta.get("categories", []),
                "published_at": paper_meta.get("published_at"),
                "chunk_index": frag.index,
                "chunk_body": frag.content,
                "section_title": frag.section_title,
                "word_count": frag.word_count,
                "embedding": vec,
            }
            actions.append(doc)

        total = 0
        for i in range(0, len(actions), _BATCH):
            batch = actions[i : i + _BATCH]
            total += self._engine.bulk_index(batch)

        log.info(
            "fragments_indexed",
            arxiv_id=fragments[0].arxiv_id,
            count=total,
        )
        return total
