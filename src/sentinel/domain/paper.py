"""Domain representation of an arXiv paper."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True, slots=True)
class PaperRecord:
    """Immutable snapshot of a paper's metadata and content."""

    arxiv_id: str
    title: str
    authors: list[str] = field(default_factory=list)
    abstract: str = ""
    categories: list[str] = field(default_factory=list)
    published: datetime | None = None
    pdf_link: str = ""
    body_text: str | None = None
    sections: list[dict[str, str]] | None = None
    references: list[str] | None = None
    parsed: bool = False
    parser_name: str | None = None
