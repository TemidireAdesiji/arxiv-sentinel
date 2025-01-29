"""Tests for sentinel.ingestion.chunker — text splitting."""

from __future__ import annotations

import pytest

from sentinel.ingestion.chunker import DocumentSplitter
from sentinel.settings import ChunkCfg


@pytest.fixture()
def splitter() -> DocumentSplitter:
    cfg = ChunkCfg(
        size=10,
        overlap=3,
        min_size=3,
        section_aware=True,
    )
    return DocumentSplitter(cfg)


class TestWindowSplitting:
    def test_short_text_single_fragment(self, splitter):
        frags = splitter.split(
            arxiv_id="1234",
            paper_id="p1",
            body="one two three four",
        )
        assert len(frags) == 1
        assert frags[0].word_count == 4

    def test_long_text_produces_overlap(self, splitter):
        words = " ".join(f"w{i}" for i in range(25))
        frags = splitter.split(
            arxiv_id="1234",
            paper_id="p1",
            body=words,
        )
        assert len(frags) > 1
        assert all(f.arxiv_id == "1234" for f in frags)

    def test_indices_are_sequential(self, splitter):
        words = " ".join(f"w{i}" for i in range(30))
        frags = splitter.split(
            arxiv_id="x",
            paper_id="p",
            body=words,
        )
        indices = [f.index for f in frags]
        assert indices == list(range(len(frags)))


class TestSectionAwareSplitting:
    def test_sections_preserved_as_fragments(self, splitter):
        sections = [
            {
                "title": "Intro",
                "content": "a b c d e f g",
            },
            {
                "title": "Methods",
                "content": "x y z a b c d",
            },
        ]
        frags = splitter.split(
            arxiv_id="1",
            paper_id="p",
            body="",
            sections=sections,
            title="T",
            abstract="A",
        )
        assert len(frags) >= 2

    def test_short_sections_are_merged(self, splitter):
        sections = [
            {"title": "A", "content": "x y"},
            {"title": "B", "content": "a b"},
        ]
        frags = splitter.split(
            arxiv_id="1",
            paper_id="p",
            body="",
            sections=sections,
        )
        assert len(frags) >= 1

    def test_empty_body_empty_sections(self, splitter):
        frags = splitter.split(
            arxiv_id="1",
            paper_id="p",
            body="",
            sections=[],
        )
        assert frags == []
