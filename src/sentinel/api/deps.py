"""FastAPI dependency-injection helpers.

Each ``resolve_*`` function pulls a service from
``request.app.state`` so routes stay decoupled from
construction details.
"""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import Depends, Request

from sentinel.settings import AppSettings, resolve_settings

# ── Settings (cached singleton) ─────────────────────

SettingsDep = Annotated[AppSettings, Depends(resolve_settings)]


# ── Request-scoped services ─────────────────────────


def _state(request: Request) -> Any:
    return request.app.state


def resolve_db(request: Request) -> Any:
    return request.app.state.db


def resolve_search(request: Request) -> Any:
    return request.app.state.search


def resolve_embedder(request: Request) -> Any:
    return request.app.state.embedder


def resolve_llm(request: Request) -> Any:
    return request.app.state.llm


def resolve_tracer(request: Request) -> Any:
    return getattr(request.app.state, "tracer", None)


def resolve_cache(request: Request) -> Any:
    return getattr(request.app.state, "cache", None)


def resolve_agent(request: Request) -> Any:
    return getattr(request.app.state, "agent", None)


DbDep = Annotated[Any, Depends(resolve_db)]
SearchDep = Annotated[Any, Depends(resolve_search)]
EmbedDep = Annotated[Any, Depends(resolve_embedder)]
LlmDep = Annotated[Any, Depends(resolve_llm)]
TracerDep = Annotated[Any, Depends(resolve_tracer)]
CacheDep = Annotated[Any, Depends(resolve_cache)]
AgentDep = Annotated[Any, Depends(resolve_agent)]
