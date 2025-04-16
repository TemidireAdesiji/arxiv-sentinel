"""Centralised configuration loaded from environment variables."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class _Base(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
    )


# ── Nested config groups ────────────────────────────


class SearchCfg(_Base):
    """OpenSearch connection and index settings."""

    model_config = SettingsConfigDict(env_prefix="SEARCH__")

    host: str = "http://localhost:9200"
    index: str = "arxiv-papers"
    chunk_suffix: str = "-chunks"
    max_text_bytes: int = 1_000_000
    vector_dim: int = 1024
    space_type: str = "cosinesimil"
    rrf_pipeline: str = "hybrid-rrf-pipeline"
    hybrid_multiplier: int = 2


class LlmCfg(_Base):
    """Ollama inference settings."""

    model_config = SettingsConfigDict(env_prefix="LLM__")

    host: str = "http://localhost:11434"
    model: str = "llama3.2:1b"
    timeout: int = 300


class ArxivCfg(_Base):
    """arXiv ingestion settings."""

    model_config = SettingsConfigDict(env_prefix="ARXIV__")

    max_papers: int = 15
    api_url: str = "https://export.arxiv.org/api/query"
    pdf_dir: str = "./data/arxiv_pdfs"
    rate_delay: float = 3.0
    timeout: int = 30
    category: str = "cs.AI"
    retries: int = 3
    retry_base: float = 5.0
    concurrency: int = 5

    @field_validator("pdf_dir")
    @classmethod
    def _ensure_dir(cls, v: str) -> str:
        Path(v).mkdir(parents=True, exist_ok=True)
        return v


class PdfCfg(_Base):
    """PDF parsing limits."""

    model_config = SettingsConfigDict(env_prefix="PDF__")

    max_pages: int = 30
    max_size_mb: int = 20
    ocr: bool = False
    table_extract: bool = True


class ChunkCfg(_Base):
    """Text-splitting parameters."""

    model_config = SettingsConfigDict(env_prefix="CHUNKING__")

    size: int = 600
    overlap: int = 100
    min_size: int = 100
    section_aware: bool = True


class CacheCfg(_Base):
    """Redis cache settings."""

    model_config = SettingsConfigDict(env_prefix="CACHE__")

    host: str = "localhost"
    port: int = 6379
    password: str = ""
    db: int = 0
    ttl_hours: int = 6


class TracingCfg(_Base):
    """Langfuse observability settings."""

    model_config = SettingsConfigDict(env_prefix="TRACING__")

    enabled: bool = False
    host: str = "http://localhost:3001"
    public_key: str = ""
    secret_key: str = ""
    flush_at: int = 15
    flush_interval: float = 1.0
    debug: bool = False


class TelegramCfg(_Base):
    """Telegram bot settings."""

    model_config = SettingsConfigDict(env_prefix="TELEGRAM__")

    enabled: bool = False
    token: str = ""


# ── Root settings ────────────────────────────────────


class AppSettings(_Base):
    """Top-level application configuration.

    Nested groups are populated from env vars using the
    double-underscore delimiter (e.g. ``SEARCH__HOST``).
    """

    app_version: str = os.getenv("APP_VERSION", "0.1.0")
    debug: bool = True
    environment: str = "development"
    service_name: str = "arxiv-sentinel"

    db_url: str = (
        "postgresql+psycopg2://sentinel:sentinel@localhost:5432/sentinel_db"
    )
    db_echo: bool = False
    db_pool_size: int = 20
    db_overflow: int = 0

    jina_api_key: str = ""

    search: SearchCfg = SearchCfg()
    llm: LlmCfg = LlmCfg()
    arxiv: ArxivCfg = ArxivCfg()
    pdf: PdfCfg = PdfCfg()
    chunking: ChunkCfg = ChunkCfg()
    cache: CacheCfg = CacheCfg()
    tracing: TracingCfg = TracingCfg()
    telegram: TelegramCfg = TelegramCfg()

    @field_validator("db_url")
    @classmethod
    def _validate_db_url(cls, v: str) -> str:
        if not v.startswith(("postgresql", "sqlite")):
            raise ValueError("db_url must start with 'postgresql' or 'sqlite'")
        return v


@lru_cache(maxsize=1)
def resolve_settings() -> AppSettings:
    """Return the cached singleton ``AppSettings`` instance."""
    return AppSettings()
