"""Langfuse trace recorder for RAG pipeline spans."""

from __future__ import annotations

import time
from typing import Any

import structlog

from sentinel.settings import TracingCfg

log = structlog.get_logger(__name__)


class TraceRecorder:
    """Wraps the Langfuse SDK to record RAG-specific spans.

    When tracing is disabled the methods are safe no-ops.
    """

    def __init__(self, cfg: TracingCfg) -> None:
        self._enabled = cfg.enabled
        self._client: Any = None
        if self._enabled:
            try:
                from langfuse import Langfuse

                self._client = Langfuse(
                    public_key=cfg.public_key,
                    secret_key=cfg.secret_key,
                    host=cfg.host,
                    flush_at=cfg.flush_at,
                    flush_interval=cfg.flush_interval,
                    debug=cfg.debug,
                )
                log.info(
                    "tracing_enabled",
                    host=cfg.host,
                )
            except Exception as exc:
                log.warning(
                    "tracing_init_failed",
                    err=str(exc),
                )
                self._enabled = False

    # -- trace lifecycle ------------------------------------------

    def begin_trace(
        self,
        name: str,
        *,
        user_id: str = "api",
        metadata: dict[str, Any] | None = None,
    ) -> _Trace:
        """Start a new top-level trace."""
        if not self._enabled:
            return _NullTrace()
        trace = self._client.trace(
            name=name,
            user_id=user_id,
            metadata=metadata or {},
        )
        return _LangfuseTrace(trace)

    # -- feedback -------------------------------------------------

    def record_feedback(
        self,
        trace_id: str,
        score: float,
        comment: str = "",
    ) -> bool:
        """Attach user feedback to an existing trace."""
        if not self._enabled:
            return False
        try:
            self._client.score(
                trace_id=trace_id,
                name="user_feedback",
                value=score,
                comment=comment,
            )
            return True
        except Exception as exc:
            log.warning("feedback_failed", err=str(exc))
            return False

    # -- shutdown -------------------------------------------------

    def flush(self) -> None:
        if self._enabled and self._client:
            self._client.flush()


class _Trace:
    """Abstract trace handle."""

    def span(
        self,
        name: str,
        **kw: Any,
    ) -> _Span:
        raise NotImplementedError

    @property
    def trace_id(self) -> str | None:
        return None


class _Span:
    """Abstract span handle."""

    def end(self, **kw: Any) -> None:
        raise NotImplementedError


class _NullTrace(_Trace):
    """No-op trace when tracing is disabled."""

    def span(self, name: str, **kw: Any) -> _Span:
        return _NullSpan()

    @property
    def trace_id(self) -> str | None:
        return None


class _NullSpan(_Span):
    def end(self, **kw: Any) -> None:
        pass


class _LangfuseTrace(_Trace):
    """Wraps a real Langfuse trace object."""

    def __init__(self, raw: Any) -> None:
        self._raw = raw

    def span(self, name: str, **kw: Any) -> _Span:
        s = self._raw.span(name=name, **kw)
        return _LangfuseSpan(s)

    @property
    def trace_id(self) -> str | None:
        return str(self._raw.id)


class _LangfuseSpan(_Span):
    """Wraps a real Langfuse span object."""

    def __init__(self, raw: Any) -> None:
        self._raw = raw
        self._t0 = time.perf_counter()

    def end(self, **kw: Any) -> None:
        elapsed = time.perf_counter() - self._t0
        kw.setdefault(
            "metadata",
            {},
        )["duration_ms"] = round(elapsed * 1000, 1)
        self._raw.end(**kw)


def create_trace_recorder(
    cfg: TracingCfg,
) -> TraceRecorder:
    """Factory: build a ``TraceRecorder``."""
    return TraceRecorder(cfg)
