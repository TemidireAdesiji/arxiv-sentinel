"""FastAPI middleware for logging and error handling."""

from __future__ import annotations

import time
import uuid

import structlog
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import (
    BaseHTTPMiddleware,
    RequestResponseEndpoint,
)

log = structlog.get_logger("sentinel.http")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log every request with timing and correlation ID."""

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        req_id = uuid.uuid4().hex[:12]
        structlog.contextvars.bind_contextvars(
            request_id=req_id,
        )

        t0 = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            log.exception(
                "unhandled_error",
                method=request.method,
                path=request.url.path,
            )
            response = JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"},
            )

        elapsed_ms = round((time.perf_counter() - t0) * 1000, 1)
        log.info(
            "http_request",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            duration_ms=elapsed_ms,
        )
        response.headers["X-Request-ID"] = req_id
        structlog.contextvars.unbind_contextvars(
            "request_id",
        )
        return response


def attach_middleware(app: FastAPI) -> None:
    """Register all middleware on *app*."""
    app.add_middleware(RequestLoggingMiddleware)
