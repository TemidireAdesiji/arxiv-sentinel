"""Application-wide exception hierarchy.

Every category of failure has its own base class so callers
can catch at whatever granularity they need.
"""

from __future__ import annotations

# ── Storage ──────────────────────────────────────────


class StorageError(Exception):
    """Base for all persistence-layer failures."""


class RecordNotFound(StorageError):
    """Requested entity does not exist."""

    def __init__(self, entity: str, identifier: str) -> None:
        self.entity = entity
        self.identifier = identifier
        super().__init__(f"{entity} with id={identifier!r} not found")


class RecordNotSaved(StorageError):
    """Write to the database failed."""


# ── PDF processing ───────────────────────────────────


class PdfError(Exception):
    """Base for PDF-related failures."""


class PdfValidationError(PdfError):
    """PDF exceeds configured limits."""


class PdfDownloadError(PdfError):
    """Could not retrieve PDF from remote URL."""


class PdfDownloadTimeout(PdfDownloadError):
    """Download exceeded the timeout."""


class PdfParseError(PdfError):
    """Parsing the PDF content failed."""


# ── Search engine ────────────────────────────────────


class SearchEngineError(Exception):
    """OpenSearch operation failed."""


class IndexCreationError(SearchEngineError):
    """Failed to create or configure an index."""


# ── External APIs ────────────────────────────────────


class ArxivApiError(Exception):
    """arXiv API returned an error or timed out."""


class ArxivRateLimited(ArxivApiError):
    """arXiv rate-limit was hit."""


class ArxivTimeout(ArxivApiError):
    """Request to arXiv timed out."""


# ── LLM / Inference ─────────────────────────────────


class InferenceError(Exception):
    """LLM inference request failed."""


class InferenceConnectionError(InferenceError):
    """Cannot reach the inference server."""


class InferenceTimeout(InferenceError):
    """Inference request exceeded timeout."""


# ── Embeddings ───────────────────────────────────────


class EmbeddingError(Exception):
    """Embedding generation failed."""


# ── Configuration ────────────────────────────────────


class ConfigError(Exception):
    """Invalid or missing configuration."""
