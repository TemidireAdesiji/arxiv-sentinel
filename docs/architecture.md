# Architecture

## System Overview

arxiv-sentinel is a layered application that separates concerns into four tiers:

```
Interface → API → Service → Infrastructure
```

### Interface Layer

Three entry-points serve different audiences:

| Interface | Technology | Use-case |
|-----------|-----------|----------|
| REST API | FastAPI | Programmatic access, CI integration |
| Gradio UI | Gradio | Interactive exploration |
| Telegram Bot | python-telegram-bot | Mobile, conversational |

### API Layer (`sentinel.api`)

FastAPI routers handle HTTP concerns: validation, serialisation, error responses.  Middleware adds request-ID headers, structured logging, and timing.  Dependency injection (via `Depends`) passes service instances from `app.state` into route handlers.

### Service Layer

Each service is a focused module with a factory function and no cross-dependencies:

- **SearchEngine** — wraps OpenSearch for BM25, vector, and hybrid queries.
- **EmbeddingProvider** — calls Jina AI to generate 1024-dim vectors.
- **InferenceClient** — calls Ollama for local LLM generation.
- **CacheStore** — Redis exact-match cache with SHA-256 key hashing.
- **TraceRecorder** — Langfuse spans for every pipeline stage.
- **AgentOrchestrator** — lightweight state-machine for multi-step reasoning.

### Infrastructure Layer

Stateful backing services managed via Docker Compose:

- **PostgreSQL 16** — paper metadata and parsed content.
- **OpenSearch 2.19** — hybrid BM25 + KNN search index.
- **Redis 7** — response cache with LRU eviction.
- **Ollama** — local LLM model serving.
- **Langfuse v3** — self-hosted observability (optional overlay).
- **Airflow** — scheduled ingestion DAG (optional overlay).

## Agentic Pipeline

The agent is a directed graph executed by `WorkflowGraph` — a ~60-line async state-machine with no external dependencies.

```
START
  │
  ▼
┌─────────────┐
│  Guardrail  │──score < 60──▶ Reject ──▶ END
└──────┬──────┘
       │ score ≥ 60
       ▼
┌─────────────┐
│  Retrieve   │◀─────────────────────┐
└──────┬──────┘                      │
       ▼                             │
┌─────────────┐                      │
│   Grade     │──not relevant────▶ Rewrite
└──────┬──────┘   (attempts < max)
       │ relevant
       ▼
┌─────────────┐
│  Generate   │──▶ END
└─────────────┘
```

Each node is a plain async function `(state, ctx) -> state`.  Routing is handled by simple Python functions that inspect `state.route` and `state.attempt_count`.

## Search Strategy

### Hybrid Search with RRF

OpenSearch's native search-pipeline feature combines BM25 and KNN results using Reciprocal Rank Fusion:

1. **BM25 leg**: `multi_match` across `title^3`, `abstract^2`, `chunk_body`.
2. **KNN leg**: cosine similarity on 1024-dim Jina embeddings.
3. **Fusion**: min-max normalisation + arithmetic mean (0.3 BM25, 0.7 vector).

### Section-Aware Chunking

Papers are split respecting document structure:

- Sections within 100–600 words → single chunk with title + abstract prepended.
- Short sections (< 100 words) → merged with neighbours.
- Long sections (> 600 words) → overlap-window split.

## Data Flow

```
arXiv API  ──fetch──▶  PostgreSQL  ──parse PDF──▶  Docling
                                                     │
                                              structured text
                                                     │
                                              ──chunk──▶ DocumentSplitter
                                                     │
                                              ──embed──▶ Jina AI
                                                     │
                                              ──index──▶ OpenSearch
```

Queries reverse the flow: embed the question, search OpenSearch, retrieve chunks, generate an answer with Ollama.
