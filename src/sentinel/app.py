"""FastAPI application factory."""

from __future__ import annotations

import os

import structlog
from fastapi import FastAPI

from sentinel.api.middleware import attach_middleware
from sentinel.api.routes import (
    ask,
    ask_agentic,
    feedback,
    health,
    search,
)
from sentinel.lifespan import lifespan

_PREFIX = "/api/v1"


def _configure_logging() -> None:
    """Set up structlog with JSON rendering in prod."""
    env = os.getenv("ENVIRONMENT", "development")
    processors: list = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]
    if env == "production":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            structlog.get_config().get("min_level", 0)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def build_application() -> FastAPI:
    """Construct and return the fully-wired FastAPI app."""
    _configure_logging()

    app = FastAPI(
        title="arxiv-sentinel",
        description=(
            "Production-grade arXiv paper discovery "
            "and question-answering with agentic RAG."
        ),
        version=os.getenv("APP_VERSION", "0.1.0"),
        lifespan=lifespan,
    )

    attach_middleware(app)

    app.include_router(health.router, prefix=_PREFIX)
    app.include_router(search.router, prefix=_PREFIX)
    app.include_router(ask.router, prefix=_PREFIX)
    app.include_router(ask.stream_router, prefix=_PREFIX)
    app.include_router(ask_agentic.router, prefix=_PREFIX)
    app.include_router(feedback.router, prefix=_PREFIX)

    return app
