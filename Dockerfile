FROM ghcr.io/astral-sh/uv:python3.12-bookworm AS builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

COPY src/ src/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev


FROM python:3.12.8-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH" \
    APP_VERSION=0.1.0

WORKDIR /app
COPY --from=builder /app /app

EXPOSE 8000

CMD [ \
    "uvicorn", "sentinel.app:build_application", \
    "--factory", \
    "--host", "0.0.0.0", \
    "--port", "8000", \
    "--workers", "4" \
]
