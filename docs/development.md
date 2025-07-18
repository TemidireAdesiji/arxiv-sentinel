# Development Guide

## Prerequisites

- Python 3.12
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- Docker & Docker Compose
- A Jina AI API key

## Initial Setup

```bash
git clone https://github.com/user/arxiv-sentinel.git
cd arxiv-sentinel
uv sync --all-groups
pre-commit install
cp .env.example .env
```

## Project Layout

```
src/sentinel/
├── app.py            # FastAPI factory + structlog config
├── lifespan.py       # Service bootstrap / shutdown
├── settings.py       # Pydantic settings (env-driven)
├── exceptions.py     # Exception hierarchy
│
├── api/              # HTTP layer
│   ├── deps.py       # Dependency injection
│   ├── middleware.py  # Request logging, error handling
│   ├── schemas.py     # Pydantic request/response models
│   └── routes/        # One module per endpoint group
│
├── agent/            # Agentic RAG state machine
│   ├── graph.py      # Generic workflow executor
│   ├── state.py      # Pipeline state dataclass
│   ├── nodes.py      # Node functions + routers
│   └── runner.py     # Top-level orchestrator
│
├── search/           # OpenSearch integration
│   ├── client.py     # Index + search operations
│   ├── queries.py    # Query DSL builder
│   ├── schema.py     # Index mapping definitions
│   └── indexer.py    # Chunk embedding + bulk index
│
├── embeddings/       # Jina AI client
├── llm/              # Ollama client + prompts
├── cache/            # Redis store
├── tracing/          # Langfuse recorder
├── ingestion/        # arXiv, PDF, chunker
├── db/               # SQLAlchemy models + repos
└── domain/           # Pure domain objects
```

## Key Patterns

### Factory Functions

Every service has a `create_*` factory function at module level.  The `lifespan.py` calls these during startup and stores instances on `app.state`.

### Dependency Injection

Routes receive services via `Annotated[T, Depends(resolver)]`.  Resolvers read from `request.app.state`.

### Structured Logging

All modules use `structlog.get_logger(__name__)`.  In development, logs render as coloured console output.  In production (`ENVIRONMENT=production`), they render as JSON.

### Agent Graph

The `WorkflowGraph` is a minimal async directed-graph executor.  Nodes are plain `async def` functions.  Edges are either static strings or router functions.  This replaces LangGraph with zero external dependencies.

## Testing Conventions

- **Unit tests** (`tests/unit/`): mock all external services.  Fast, no Docker required.
- **API tests** (`tests/api/`): use `httpx.AsyncClient` with mocked lifespan.  Tests the full HTTP stack.
- **Integration tests** (`tests/integration/`): require running Docker services.  Marked with `@pytest.mark.integration`.

Run unit + API tests:

```bash
make test
```

Run all tests including integration:

```bash
make start
make test-int
```

## Adding a New Endpoint

1. Define request/response models in `api/schemas.py`.
2. Create a new route module in `api/routes/`.
3. Register the router in `app.py`.
4. Add tests in `tests/api/`.

## Adding a New Service

1. Create a module under `src/sentinel/` (e.g. `src/sentinel/newservice/`).
2. Implement a client class + `create_*` factory.
3. Wire it into `lifespan.py` (store on `app.state`).
4. Add a resolver in `api/deps.py`.
5. Add unit tests with mocked dependencies.
