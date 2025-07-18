# API Reference

Base URL: `http://localhost:8000/api/v1`

Interactive docs: `http://localhost:8000/docs` (Swagger UI)

## Endpoints

### `GET /health`

Returns the health status of all backing services.

**Response** `200 OK`:
```json
{
  "status": "ok",
  "version": "0.1.0",
  "environment": "development",
  "service_name": "arxiv-sentinel",
  "services": {
    "database": { "status": "healthy", "message": "Connected" },
    "opensearch": { "status": "healthy", "message": "docs=150" },
    "ollama": { "status": "healthy", "message": "0.11.2" }
  }
}
```

---

### `POST /search`

Execute a hybrid or BM25 search over indexed paper chunks.

**Request body**:
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `query` | string | *required* | Search text (1–1000 chars) |
| `size` | int | `10` | Results per page (1–100) |
| `offset` | int | `0` | Pagination offset |
| `hybrid` | bool | `true` | Use hybrid search |
| `categories` | string[] | `null` | Filter by arXiv category |
| `latest_only` | bool | `false` | Last 7 days only |
| `min_score` | float | `null` | Minimum relevance score |

**Response** `200 OK`:
```json
{
  "query": "retrieval augmented generation",
  "mode": "hybrid",
  "total": 42,
  "hits": [
    {
      "arxiv_id": "2401.00001",
      "title": "Paper Title",
      "authors": ["Author A"],
      "abstract": "...",
      "score": 0.95,
      "chunk_text": "..."
    }
  ]
}
```

---

### `POST /ask`

Answer a question using retrieved paper context (standard RAG).

**Request body**:
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `query` | string | *required* | Question (1–1000 chars) |
| `top_k` | int | `3` | Number of chunks to retrieve (1–10) |
| `hybrid` | bool | `true` | Use hybrid search |
| `model` | string | `llama3.2:1b` | Ollama model name |
| `categories` | string[] | `null` | Category filter |

**Response** `200 OK`:
```json
{
  "query": "What is RAG?",
  "answer": "RAG (Retrieval-Augmented Generation) is...",
  "sources": ["https://arxiv.org/abs/2401.00001"],
  "chunks_used": 3,
  "mode": "hybrid",
  "trace_id": "abc-123"
}
```

---

### `POST /stream`

Same as `/ask` but returns Server-Sent Events for token-by-token streaming.

**Events**:
- `metadata` — JSON with sources, chunks_used, mode
- `token` — individual text token
- `done` — stream complete

---

### `POST /ask-agentic`

Multi-step agentic RAG with reasoning transparency.

**Request body**: same as `/ask`.

**Response** `200 OK`:
```json
{
  "query": "Compare dense and sparse retrieval",
  "answer": "Dense retrieval uses...",
  "sources": ["https://arxiv.org/abs/2401.00001"],
  "reasoning_steps": [
    "Guardrail score: 92/100",
    "Retrieval attempt 1: 'Compare dense and sparse retrieval'",
    "3 relevant document(s) found",
    "Answer generated from 3 chunk(s)"
  ],
  "retrieval_attempts": 1,
  "trace_id": "trace-456"
}
```

---

### `POST /feedback`

Attach user feedback to a traced request.

**Request body**:
| Field | Type | Description |
|-------|------|-------------|
| `trace_id` | string | *required* — ID from a previous response |
| `score` | float | *required* — 0.0 to 1.0 |
| `comment` | string | Optional free-text |

**Response** `200 OK`:
```json
{ "success": true }
```
