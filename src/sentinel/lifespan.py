"""FastAPI lifespan: bootstrap and tear-down services."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI

from sentinel.agent.runner import (
    create_agent_orchestrator,
)
from sentinel.cache.redis import create_cache_store
from sentinel.db.engine import create_database_gateway
from sentinel.db.models import Base
from sentinel.embeddings.jina import (
    create_embedding_provider,
)
from sentinel.ingestion.arxiv import (
    create_arxiv_fetcher,
)
from sentinel.ingestion.pdf import (
    create_pdf_extractor,
)
from sentinel.llm.client import (
    create_inference_client,
)
from sentinel.search.client import create_search_engine
from sentinel.settings import resolve_settings
from sentinel.tracing.langfuse import (
    create_trace_recorder,
)

log = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(
    app: FastAPI,
) -> AsyncIterator[None]:
    """Initialise all services on startup, clean up on shutdown."""
    cfg = resolve_settings()
    log.info(
        "startup_begin",
        env=cfg.environment,
        version=cfg.app_version,
    )

    # ── Database ─────────────────────────────────
    db = create_database_gateway(cfg)
    if db.verify_connection():
        Base.metadata.create_all(
            bind=db._engine  # noqa: SLF001
        )
        log.info("database_connected")
    else:
        log.warning("database_unreachable")
    app.state.db = db

    # ── Search engine ────────────────────────────
    search = create_search_engine(cfg.search)
    try:
        search.ensure_index()
        log.info("search_engine_ready")
    except Exception:
        log.warning("search_index_setup_failed")
    app.state.search = search

    # ── Embeddings ───────────────────────────────
    embedder = create_embedding_provider(cfg.jina_api_key)
    app.state.embedder = embedder

    # ── LLM ──────────────────────────────────────
    llm = create_inference_client(cfg.llm)
    app.state.llm = llm

    # ── Tracing ──────────────────────────────────
    tracer = create_trace_recorder(cfg.tracing)
    app.state.tracer = tracer

    # ── Cache ────────────────────────────────────
    cache = create_cache_store(cfg.cache)
    app.state.cache = cache

    # ── arXiv / PDF (for pipeline use) ───────────
    app.state.arxiv = create_arxiv_fetcher(cfg.arxiv)
    app.state.pdf = create_pdf_extractor(cfg.pdf)

    # ── Agent ────────────────────────────────────
    agent = create_agent_orchestrator(
        search=search,
        embedder=embedder,
        llm=llm,
        tracer=tracer,
    )
    app.state.agent = agent

    # ── Telegram (optional) ──────────────────────
    tg_bot = None
    if cfg.telegram.enabled and cfg.telegram.token:
        try:
            from sentinel.telegram import (
                create_sentinel_bot,
            )

            tg_bot = create_sentinel_bot(
                token=cfg.telegram.token,
                agent=agent,
            )
            await tg_bot.start()
            log.info("telegram_bot_started")
        except Exception:
            log.warning("telegram_bot_failed")
    app.state.telegram = tg_bot

    log.info("startup_complete")
    yield

    # ── Shutdown ─────────────────────────────────
    log.info("shutdown_begin")
    if tg_bot:
        await tg_bot.stop()
    if cache:
        cache.close()
    await embedder.close()
    await llm.close()
    tracer.flush()
    db.dispose()
    log.info("shutdown_complete")
