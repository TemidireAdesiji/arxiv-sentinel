"""Domain representation of a text fragment (chunk)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TextFragment:
    """One contiguous chunk of paper text with metadata."""

    arxiv_id: str
    paper_id: str
    index: int
    content: str
    word_count: int
    section_title: str = ""
    start_char: int = 0
    end_char: int = 0
