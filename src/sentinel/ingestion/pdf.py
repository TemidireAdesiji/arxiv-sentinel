"""PDF content extractor using the Docling library."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import structlog

from sentinel.exceptions import (
    PdfParseError,
    PdfValidationError,
)
from sentinel.settings import PdfCfg

log = structlog.get_logger(__name__)

_MB = 1024 * 1024


class PdfExtractor:
    """Parse scientific PDFs into structured sections."""

    def __init__(self, cfg: PdfCfg) -> None:
        self._max_pages = cfg.max_pages
        self._max_bytes = cfg.max_size_mb * _MB
        self._ocr = cfg.ocr
        self._tables = cfg.table_extract

    def validate(self, path: Path) -> None:
        """Raise ``PdfValidationError`` if limits exceeded."""
        if not path.exists():
            raise PdfValidationError(f"File not found: {path}")
        size = path.stat().st_size
        if size > self._max_bytes:
            raise PdfValidationError(
                f"PDF too large: {size / _MB:.1f} MB "
                f"(limit {self._max_bytes / _MB} MB)"
            )

    def extract(self, path: Path) -> dict[str, Any]:
        """Parse *path* and return structured content.

        Returns a dict with keys ``body``, ``sections``,
        and ``meta``.
        """
        self.validate(path)
        try:
            from docling.document_converter import (
                DocumentConverter,
            )

            converter = DocumentConverter()
            result = converter.convert(str(path))
            doc = result.document

            body = doc.export_to_markdown()
            sections = self._extract_sections(doc)

            log.info(
                "pdf_extracted",
                path=str(path),
                sections=len(sections),
            )
            return {
                "body": body,
                "sections": sections,
                "meta": {
                    "parser": "docling",
                    "pages": getattr(doc, "page_count", None),
                },
            }
        except PdfValidationError:
            raise
        except Exception as exc:
            log.error(
                "pdf_parse_failed",
                path=str(path),
                err=str(exc),
            )
            raise PdfParseError(str(exc)) from exc

    @staticmethod
    def _extract_sections(
        doc: Any,
    ) -> list[dict[str, str]]:
        sections: list[dict[str, str]] = []
        try:
            for item in doc.iterate_items():
                label = getattr(item, "label", "")
                text = getattr(item, "text", "")
                if label and text:
                    sections.append(
                        {
                            "title": str(label),
                            "content": str(text),
                        }
                    )
        except Exception:
            pass
        return sections


def create_pdf_extractor(
    cfg: PdfCfg,
) -> PdfExtractor:
    """Factory: build a ``PdfExtractor``."""
    return PdfExtractor(cfg)
