"""Section-aware text splitter for indexed documents."""

from __future__ import annotations

import structlog

from sentinel.domain.chunk import TextFragment
from sentinel.settings import ChunkCfg

log = structlog.get_logger(__name__)


class DocumentSplitter:
    """Split paper text into overlapping word-chunks.

    When ``section_aware`` is *True* and structured sections
    are available, the splitter preserves section boundaries:

    * Sections within ``[min_size, size]`` words become a
      single fragment (with title + abstract prepended).
    * Sections shorter than ``min_size`` are merged with
      neighbours.
    * Sections longer than ``size`` are split using the
      overlap window.
    """

    def __init__(self, cfg: ChunkCfg) -> None:
        self._size = cfg.size
        self._overlap = cfg.overlap
        self._min = cfg.min_size
        self._section_aware = cfg.section_aware

    def split(
        self,
        *,
        arxiv_id: str,
        paper_id: str,
        body: str,
        sections: list[dict[str, str]] | None = None,
        title: str = "",
        abstract: str = "",
    ) -> list[TextFragment]:
        """Return a list of ``TextFragment`` objects."""
        if self._section_aware and sections and len(sections) > 1:
            return self._split_by_section(
                arxiv_id=arxiv_id,
                paper_id=paper_id,
                sections=sections,
                title=title,
                abstract=abstract,
            )
        return self._split_by_window(
            arxiv_id=arxiv_id,
            paper_id=paper_id,
            text=body,
        )

    # -- section-aware splitting ----------------------------------

    def _split_by_section(
        self,
        *,
        arxiv_id: str,
        paper_id: str,
        sections: list[dict[str, str]],
        title: str,
        abstract: str,
    ) -> list[TextFragment]:
        preamble = ""
        if title:
            preamble += f"Title: {title}\n"
        if abstract:
            preamble += f"Abstract: {abstract}\n\n"

        fragments: list[TextFragment] = []
        buffer = ""
        buffer_title = ""
        idx = 0

        for sec in sections:
            sec_title = sec.get("title", "")
            sec_body = sec.get("content", "")
            words = len(sec_body.split())

            if words > self._size:
                if buffer:
                    fragments.extend(
                        self._emit(
                            arxiv_id,
                            paper_id,
                            preamble + buffer,
                            buffer_title,
                            idx,
                        )
                    )
                    idx += len(fragments) - idx
                    buffer = ""
                    buffer_title = ""
                sub = self._split_by_window(
                    arxiv_id=arxiv_id,
                    paper_id=paper_id,
                    text=preamble + sec_body,
                    start_index=idx,
                    section_title=sec_title,
                )
                fragments.extend(sub)
                idx += len(sub)
            elif words < self._min:
                if buffer:
                    buffer += "\n\n"
                buffer += sec_body
                if not buffer_title:
                    buffer_title = sec_title
            else:
                if buffer:
                    merged = buffer + "\n\n" + sec_body
                    if len(merged.split()) <= self._size:
                        buffer = merged
                        continue
                    fragments.extend(
                        self._emit(
                            arxiv_id,
                            paper_id,
                            preamble + buffer,
                            buffer_title,
                            idx,
                        )
                    )
                    idx += len(fragments) - idx
                    buffer = ""
                    buffer_title = ""
                fragments.extend(
                    self._emit(
                        arxiv_id,
                        paper_id,
                        preamble + sec_body,
                        sec_title,
                        idx,
                    )
                )
                idx += len(fragments) - idx

        if buffer:
            fragments.extend(
                self._emit(
                    arxiv_id,
                    paper_id,
                    preamble + buffer,
                    buffer_title,
                    idx,
                )
            )

        log.info(
            "split_by_section",
            arxiv_id=arxiv_id,
            fragments=len(fragments),
        )
        return fragments

    # -- window splitting -----------------------------------------

    def _split_by_window(
        self,
        *,
        arxiv_id: str,
        paper_id: str,
        text: str,
        start_index: int = 0,
        section_title: str = "",
    ) -> list[TextFragment]:
        words = text.split()
        if not words:
            return []

        frags: list[TextFragment] = []
        pos = 0
        idx = start_index
        while pos < len(words):
            end = pos + self._size
            chunk_words = words[pos:end]
            content = " ".join(chunk_words)
            char_start = (
                text.index(
                    chunk_words[0],
                    max(0, pos - 1),
                )
                if chunk_words
                else 0
            )
            frags.append(
                TextFragment(
                    arxiv_id=arxiv_id,
                    paper_id=paper_id,
                    index=idx,
                    content=content,
                    word_count=len(chunk_words),
                    section_title=section_title,
                    start_char=char_start,
                    end_char=char_start + len(content),
                )
            )
            idx += 1
            pos = end - self._overlap
            if pos <= (end - self._size):
                break
        return frags

    # -- helpers --------------------------------------------------

    def _emit(
        self,
        arxiv_id: str,
        paper_id: str,
        text: str,
        section_title: str,
        start_index: int,
    ) -> list[TextFragment]:
        words = text.split()
        if len(words) <= self._size:
            return [
                TextFragment(
                    arxiv_id=arxiv_id,
                    paper_id=paper_id,
                    index=start_index,
                    content=text,
                    word_count=len(words),
                    section_title=section_title,
                )
            ]
        return self._split_by_window(
            arxiv_id=arxiv_id,
            paper_id=paper_id,
            text=text,
            start_index=start_index,
            section_title=section_title,
        )


def create_document_splitter(
    cfg: ChunkCfg,
) -> DocumentSplitter:
    """Factory: build a ``DocumentSplitter``."""
    return DocumentSplitter(cfg)
