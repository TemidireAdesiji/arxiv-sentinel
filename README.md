<p align="center"><img src="assets/banner.png" alt="arXiv Sentinel"/></p>

<h1 align="center">arXiv Sentinel</h1>
<p align="center">Production-grade agentic RAG system for discovering and answering questions about recent arXiv papers</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white" alt="Python 3.12" />
  <img src="https://img.shields.io/badge/FastAPI-0.115+-009688?logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white" alt="Docker Compose" />
  <img src="https://img.shields.io/badge/OpenSearch-2.19-005EB8?logo=opensearch&logoColor=white" alt="OpenSearch" />
  <img src="https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white" alt="PostgreSQL" />
  <img src="https://img.shields.io/badge/Redis-7-DC382D?logo=redis&logoColor=white" alt="Redis" />
  <img src="https://img.shields.io/badge/Ollama-Local_LLM-000000" alt="Ollama" />
  <img src="https://img.shields.io/badge/License-MIT-green" alt="MIT License" />
</p>

<p align="center">
  <a href="#what-it-does">What it does</a> &bull;
  <a href="#architecture">Architecture</a> &bull;
  <a href="#tech-stack">Tech stack</a> &bull;
  <a href="#quick-start">Quick start</a> &bull;
  <a href="#configuration">Configuration</a> &bull;
  <a href="#api-reference">API reference</a> &bull;
  <a href="#agentic-pipeline">Agentic pipeline</a> &bull;
  <a href="#observability">Observability</a> &bull;
  <a href="#local-development">Local development</a> &bull;
  <a href="#known-limitations">Known limitations</a> &bull;
  <a href="#design-decisions">Design decisions</a> &bull;
  <a href="#contributing">Contributing</a>
</p>

---

## What it does

arXiv Sentinel fetches recent papers from arXiv, parses their PDFs, builds a hybrid search index, and lets you ask natural-language questions about that research. It answers via two modes:

- **Standard RAG** -- one-shot retrieve + generate, with optional token streaming
- **Agentic RAG** -- a multi-step agent that checks query quality, grades retrieved documents for relevance, rewrites the query if needed, and generates a final answer with full reasoning trace

The system is designed to be deployed with Docker Compose and includes optional Langfuse tracing, Redis caching, a Gradio web UI, a Telegram bot, and an Airflow pipeline for scheduled daily ingestion.

---

## Architecture

<p align="center"><img src="assets/architecture.png" alt="arXiv Sentinel architecture" width="800" /></p>
<!-- Regenerate with: PATH="/home/devbot/miniconda3/bin:$PATH" python scripts/gen_architecture.py -->

The system has two distinct flows:

**Ingestion** -- The Airflow DAG (or manual scripts) fetches paper metadata from the arXiv Atom feed, downloads PDFs, parses them with Docling, splits text into section-aware chunks, embeds each chunk via Jina AI, and indexes everything into OpenSearch. Paper metadata and parsed text are also persisted in PostgreSQL.

**Query** -- An API request hits FastAPI, optionally checks Redis for a cached response, embeds the query via Jina AI, executes a hybrid BM25 + KNN search against OpenSearch, then passes retrieved chunks to Ollama for answer generation. The agentic route wraps this in a state-machine loop that can rewrite the query and re-retrieve up to two times before generating.

---

## Tech stack

| Layer | Technology |
|-------|-----------|
| API framework | FastAPI 0.115+ / Uvicorn (4 workers) |
| Database | PostgreSQL 16 + SQLAlchemy 2.0 |
| Search | OpenSearch 2.19 (hybrid BM25 + HNSW KNN + RRF) |
| Embeddings | Jina AI v3 (1024-dim, task-typed) |
| LLM | Ollama (Llama 3.2:1b, local) |
| Cache | Redis 7 (SHA-256 keyed, 6h TTL) |
| Tracing | Langfuse v3 (optional) |
| Logging | Structlog 24+ (JSON in production) |
| Validation | Pydantic 2.0 |
| PDF parsing | Docling 2.0 (optional extra) |
| Web UI | Gradio 4.0 (optional extra) |
| Messaging | python-telegram-bot 21 (optional) |
| Scheduling | Apache Airflow (optional) |
| Package manager | uv |

---

## Quick start

**Requirements:** Docker, Docker Compose, a [Jina AI API key](https://jina.ai) (free tier available).

```bash
# 1. Clone and configure
git clone <repo-url> arxiv-sentinel
cd arxiv-sentinel
cp .env.example .env
# Edit .env and set JINA_API_KEY=jina_...

# 2. Start core services (API + PostgreSQL + OpenSearch + Redis + Ollama)
make start

# 3. Pull the default LLM into Ollama (first run only)
bash scripts/pull_model.sh

# 4. Verify everything is healthy
curl http://localhost:8000/api/v1/health

# 5. Ask a question
curl -s -X POST http://localhost:8000/api/v1/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the latest advances in retrieval-augmented generation?"}' \
  | python3 -m json.tool
```

The interactive API docs are at `http://localhost:8000/docs`.

### Optional stacks

```bash
make start-obs   # + Langfuse tracing dashboard (http://localhost:3001)
make start-all   # + Airflow scheduler (http://localhost:8080)
```

### Gradio web UI

```bash
uv run python launch_ui.py
# Opens http://localhost:7861
```

<!-- TODO: capture screenshot of Gradio UI -- run `python scripts/capture_screenshots.py` once the app is running -->

---

## Configuration

All settings are loaded from environment variables. Copy `.env.example` to `.env` and fill in the required values.

### Required

| Variable | Description | Example |
|----------|-------------|---------|
| `JINA_API_KEY` | Jina AI embedding API key | `jina_abc123...` |
| `DB_URL` | PostgreSQL connection string | `postgresql+psycopg2://sentinel:sentinel@localhost:5432/sentinel_db` |

### Application

| Variable | Default | Description |
|----------|---------|-------------|
| `ENVIRONMENT` | `development` | `development`, `staging`, or `production` |
| `DEBUG` | `true` | Enable debug logging |
| `SERVICE_NAME` | `arxiv-sentinel` | Service identifier in logs and traces |

### Search (OpenSearch)

| Variable | Default | Description |
|----------|---------|-------------|
| `SEARCH__HOST` | `http://localhost:9200` | OpenSearch endpoint |
| `SEARCH__INDEX` | `arxiv-papers` | Base index name |
| `SEARCH__VECTOR_DIM` | `1024` | Embedding dimension (must match Jina v3) |
| `SEARCH__HYBRID_MULTIPLIER` | `2` | Oversampling factor for hybrid search |

### LLM (Ollama)

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM__HOST` | `http://localhost:11434` | Ollama endpoint |
| `LLM__MODEL` | `llama3.2:1b` | Model name to use for generation |
| `LLM__TIMEOUT` | `300` | Inference timeout in seconds |

### Ingestion (arXiv)

| Variable | Default | Description |
|----------|---------|-------------|
| `ARXIV__CATEGORY` | `cs.AI` | arXiv category filter (e.g. `cs.AI`, `stat.ML`) |
| `ARXIV__MAX_PAPERS` | `15` | Papers to fetch per run |
| `ARXIV__RATE_DELAY` | `3.0` | Delay between arXiv API calls (seconds) |
| `ARXIV__PDF_DIR` | `./data/arxiv_pdfs` | Local PDF download directory |

### Cache (Redis)

| Variable | Default | Description |
|----------|---------|-------------|
| `CACHE__HOST` | `localhost` | Redis hostname |
| `CACHE__PORT` | `6379` | Redis port |
| `CACHE__TTL_HOURS` | `6` | Response cache lifetime |

### Tracing (Langfuse -- optional)

| Variable | Default | Description |
|----------|---------|-------------|
| `TRACING__ENABLED` | `false` | Enable Langfuse spans |
| `TRACING__HOST` | `http://localhost:3001` | Langfuse server URL |
| `TRACING__PUBLIC_KEY` | | Langfuse public key |
| `TRACING__SECRET_KEY` | | Langfuse secret key |

### Telegram bot (optional)

| Variable | Default | Description |
|----------|---------|-------------|
| `TELEGRAM__ENABLED` | `false` | Enable the bot |
| `TELEGRAM__TOKEN` | | Bot token from @BotFather |

Full reference with all defaults is in [`.env.example`](.env.example).

---

## API reference

Base URL: `http://localhost:8000/api/v1`

Interactive docs: `http://localhost:8000/docs`

### `GET /health`

Returns the status of all dependent services.

```json
{
  "status": "ok",
  "version": "0.1.0",
  "environment": "development",
  "service_name": "arxiv-sentinel",
  "services": {
    "database":   { "status": "healthy", "message": "connected" },
    "opensearch": { "status": "healthy", "message": "docs=1234" },
    "ollama":     { "status": "healthy", "message": "0.11.2" }
  }
}
```

`status` is `"degraded"` if any service is unhealthy.

---

### `POST /search`

Hybrid or BM25 search over indexed paper chunks.

**Request**
```json
{
  "query":       "retrieval augmented generation",
  "size":        10,
  "offset":      0,
  "hybrid":      true,
  "categories":  ["cs.AI", "stat.ML"],
  "latest_only": false,
  "min_score":   null
}
```

**Response**
```json
{
  "query":  "retrieval augmented generation",
  "mode":   "hybrid",
  "total":  42,
  "hits": [
    {
      "arxiv_id":  "2401.00001",
      "title":     "Advances in RAG",
      "authors":   ["Author A", "Author B"],
      "abstract":  "We propose ...",
      "score":     0.95,
      "chunk_text": "Dense retrieval encodes ..."
    }
  ]
}
```

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `query` | string | required | 1-1000 characters |
| `size` | int | `10` | 1-100 |
| `offset` | int | `0` | Pagination offset |
| `hybrid` | bool | `true` | `false` for BM25-only |
| `categories` | string[] | `null` | Filter by arXiv category |
| `latest_only` | bool | `false` | Restrict to last 7 days |

---

### `POST /ask`

Retrieve relevant chunks and generate an answer in one call.

**Request**
```json
{
  "query":      "What is retrieval-augmented generation?",
  "top_k":      3,
  "hybrid":     true,
  "model":      "llama3.2:1b",
  "categories": null
}
```

**Response**
```json
{
  "query":       "What is retrieval-augmented generation?",
  "answer":      "RAG is a technique that ...",
  "sources":     ["https://arxiv.org/abs/2401.00001"],
  "chunks_used": 3,
  "mode":        "hybrid",
  "trace_id":    "abc-123"
}
```

---

### `POST /stream`

Same as `/ask` but returns tokens as Server-Sent Events.

```
event: metadata
data: {"sources": ["https://arxiv.org/abs/2401.00001"], "chunks_used": 3, "mode": "hybrid"}

event: token
data:  Retrieval

event: token
data: -Augmented

event: done
data:
```

---

### `POST /ask-agentic`

Multi-step agentic RAG with query rewriting and relevance grading.

**Request** -- same shape as `/ask`.

**Response**
```json
{
  "query":    "Compare dense and sparse retrieval",
  "answer":   "Dense retrieval uses learned embeddings to ...",
  "sources":  ["https://arxiv.org/abs/2401.00002"],
  "reasoning_steps": [
    "Guardrail score: 92/100 (query accepted)",
    "Retrieval attempt 1: 'Compare dense and sparse retrieval'",
    "Grade: 2 relevant document(s) found",
    "Refined query: 'dense retrieval vs sparse retrieval BM25'",
    "Retrieval attempt 2: 'dense retrieval vs sparse retrieval BM25'",
    "Grade: 4 relevant document(s) found",
    "Answer generated from 4 chunk(s)"
  ],
  "retrieval_attempts": 2,
  "trace_id": "trace-456"
}
```

---

### `POST /feedback`

Attach a user rating to a traced response. Requires `TRACING__ENABLED=true`.

**Request**
```json
{
  "trace_id": "trace-456",
  "score":    0.9,
  "comment":  "Very accurate"
}
```

**Response**
```json
{ "success": true }
```

---

## Agentic pipeline

The agentic route runs a lightweight state machine (`sentinel.agent.graph.WorkflowGraph`) with the following nodes:

```
START
  └── guardrail
        ├── [score < 60] reject → END
        └── [score >= 60] retrieve
              └── grade
                    ├── [not relevant, attempts < 2] rewrite → retrieve
                    └── [relevant] generate → END
```

| Node | What it does |
|------|-------------|
| `guardrail` | Scores the query (0-100). Rejects queries that score below 60 (very short, nonsensical, or off-topic). |
| `retrieve` | Embeds the current query, searches OpenSearch, stores matching chunks in state. |
| `grade` | Asks the LLM to rate each retrieved chunk as relevant or not. Routes to `rewrite` if coverage is insufficient. |
| `rewrite` | Asks the LLM to produce a better search query, stores it in state, increments the attempt counter. |
| `generate` | Builds a RAG prompt from the final chunk set and calls Ollama for the answer. |

The maximum retrieval attempts before forced generation is 2 (configurable in `AgentOrchestrator`).

---

## Observability

### Structured logging

Structlog outputs JSON in `production` and human-readable console output otherwise. Every log entry carries a `request_id` correlation header.

Key log events:

| Event | Fields |
|-------|--------|
| `http_request` | method, path, status, duration_ms |
| `search_executed` | query, mode, total |
| `cache_hit` / `cache_miss` | query hash |
| `arxiv_fetched` | category, count |
| `agent_pipeline_failed` | exception details |

### Langfuse tracing (optional)

Enable with `TRACING__ENABLED=true` and valid Langfuse credentials. Start the Langfuse stack:

```bash
make start-obs
# Dashboard at http://localhost:3001
```

Each `/ask`, `/ask-agentic`, and `/stream` request creates a trace. The `/feedback` endpoint attaches a score to a trace by ID.

### Benchmarks

<!-- BEGIN:benchmarks -->
| Endpoint | p50 | p95 | p99 | Mean |
|----------|-----|-----|-----|------|
| POST /search | -- | -- | -- | -- |
| POST /ask | -- | -- | -- | -- |
| POST /ask-agentic | -- | -- | -- | -- |
<!-- END:benchmarks -->

Run `python scripts/benchmark.py` with the app running to populate this table.

---

## Local development

### Setup

```bash
# Install all dependencies including dev and optional extras
make setup

# Or manually with uv
uv sync --all-groups --all-extras
```

### Run without Docker

Start the backing services first (`docker compose up -d postgres opensearch redis ollama`), then:

```bash
uv run uvicorn sentinel.app:build_application --factory --reload --port 8000
```

### Testing

```bash
make test          # Unit + API tests (no services required)
make test-cov      # With HTML coverage report
make test-int      # Integration tests (requires docker compose up -d)

# Run a single test file
uv run pytest tests/unit/test_chunker.py -v
```

### Linting and type checking

```bash
make format        # Auto-format with ruff
make lint          # Lint + auto-fix with ruff
make typecheck     # mypy strict checks
```

### Gotchas

**Ollama model not found on first run.** Ollama starts but has no models downloaded. Pull the default before making any `/ask` requests:

```bash
bash scripts/pull_model.sh
# Or for a different model:
bash scripts/pull_model.sh mistral sentinel-ollama
```

**OpenSearch RRF pipeline.** The hybrid search pipeline is created automatically on the first `/search` or `/ask` request via `SearchEngine.ensure_index()`. If OpenSearch is slow to start, the first request may fail with a 503. Retry after a few seconds.

**Jina AI free tier limits.** The free tier has a rate limit on embedding calls. For large ingestion runs, consider batching with delays or upgrading to a paid tier.

**PDF extras not installed by default.** Ingestion with PDF parsing requires the `pdf` extra:

```bash
uv sync --extra pdf
```

**Gradio UI extra.** The web interface requires the `ui` extra:

```bash
uv sync --extra ui
python launch_ui.py
```

**Port conflicts.** Default ports assume no other local services. If PostgreSQL is already running on 5432, edit `compose.yml` before starting.

---

## Known limitations

- **No API authentication.** The REST API has no auth layer. It is intended for trusted internal environments. Add OAuth2 or API key middleware before exposing it publicly.
- **Exact-match cache only.** The Redis cache uses a SHA-256 hash of query parameters. Semantically similar but textually different queries always miss the cache.
- **Single-node OpenSearch.** The compose setup runs a single OpenSearch node. It is not suitable for high-availability production deployments.
- **Ollama single-instance.** There is no load balancing across Ollama instances. Concurrent inference requests queue behind each other.
- **No schema migrations.** The PostgreSQL schema is created via `Base.metadata.create_all()` at startup. There are no Alembic migration files tracked in the repo. Changing models on an existing database requires manual intervention.
- **Guardrail is simplistic.** The agent guardrail scores queries by length and character patterns rather than a dedicated safety model. It is not a robust content filter.
- **Airflow DAG has no data quality checks.** The ingestion DAG does not validate paper content or deduplication beyond `arxiv_id`.

---

## Design decisions

**Custom WorkflowGraph instead of LangGraph.** The agent graph is a ~60-line state machine written from scratch. LangGraph was intentionally avoided to eliminate a heavy dependency and make the control flow easy to trace and test without framework magic. Nodes are plain async functions `(state, ctx) -> state`.

**Hybrid BM25 + KNN with RRF.** Keyword search and vector search retrieve different relevant documents. Combining them with Reciprocal Rank Fusion (0.3 BM25 + 0.7 KNN weights) consistently outperforms either alone on academic text. The fusion is computed inside OpenSearch as a native pipeline, not on the client side.

**Section-aware chunking.** Fixed-window chunking splits mid-sentence across section boundaries. The `DocumentSplitter` respects document structure: sections under 100 words are merged with neighbors; sections over 600 words are split with 100-word overlap; every chunk is prefixed with the paper title and abstract to ensure retrieval context is self-contained.

**Jina AI task-typed embeddings.** Jina v3 uses different task parameters for queries (`retrieval.query`) and passages (`retrieval.passage`). Using the correct task type improves retrieval precision compared to a single generic embedding function.

**Temperature 0.0 for generation.** All LLM calls use `temperature=0.0` for deterministic, reproducible answers. The agent grading and rewrite steps benefit from consistent behavior across multiple calls on the same query.

**Optional services fail gracefully.** Redis, Langfuse, and Telegram are all initialized at startup but any failure there does not block the API. The cache client exposes `is_available()` and the tracer returns a `_NullTrace()` stub when disabled or unreachable. The health endpoint reports `"degraded"` rather than `500`.

---

## Contributing

Pull requests are welcome. Please run the full test and lint suite before opening a PR:

```bash
make format
make lint
make typecheck
make test
```

For larger changes, open an issue first to discuss the approach.

---

## License

[MIT](LICENSE)
