# Configuration Reference

All settings are read from environment variables.  Nested groups use the `__` delimiter (e.g. `SEARCH__HOST`).

Copy `.env.example` to `.env` and edit as needed.

## Application

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `APP_VERSION` | str | `0.1.0` | Reported in health endpoint |
| `DEBUG` | bool | `true` | Enable debug logging |
| `ENVIRONMENT` | str | `development` | `development`, `staging`, `production` |
| `SERVICE_NAME` | str | `arxiv-sentinel` | Service identifier in traces |

## Database (PostgreSQL)

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `DB_URL` | str | `postgresql+psycopg2://...` | SQLAlchemy connection string |
| `DB_ECHO` | bool | `false` | Log all SQL statements |
| `DB_POOL_SIZE` | int | `20` | Connection pool size |
| `DB_OVERFLOW` | int | `0` | Max overflow connections |

## Search Engine (OpenSearch)

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `SEARCH__HOST` | str | `http://localhost:9200` | OpenSearch endpoint |
| `SEARCH__INDEX` | str | `arxiv-papers` | Base index name |
| `SEARCH__CHUNK_SUFFIX` | str | `-chunks` | Suffix for chunk index |
| `SEARCH__VECTOR_DIM` | int | `1024` | Embedding dimension |
| `SEARCH__SPACE_TYPE` | str | `cosinesimil` | KNN space type |
| `SEARCH__RRF_PIPELINE` | str | `hybrid-rrf-pipeline` | Search pipeline name |
| `SEARCH__HYBRID_MULTIPLIER` | int | `2` | Size multiplier for hybrid |

## LLM Inference (Ollama)

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `LLM__HOST` | str | `http://localhost:11434` | Ollama endpoint |
| `LLM__MODEL` | str | `llama3.2:1b` | Default model |
| `LLM__TIMEOUT` | int | `300` | Request timeout (seconds) |

## Embeddings (Jina AI)

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `JINA_API_KEY` | str | — | **Required.** Jina AI API key |

## arXiv Ingestion

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `ARXIV__MAX_PAPERS` | int | `15` | Papers per fetch |
| `ARXIV__API_URL` | str | arXiv API | Base API URL |
| `ARXIV__PDF_DIR` | str | `./data/arxiv_pdfs` | PDF download directory |
| `ARXIV__RATE_DELAY` | float | `3.0` | Delay between API calls |
| `ARXIV__CATEGORY` | str | `cs.AI` | arXiv category filter |
| `ARXIV__RETRIES` | int | `3` | Max download retries |
| `ARXIV__CONCURRENCY` | int | `5` | Concurrent downloads |

## PDF Parsing

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `PDF__MAX_PAGES` | int | `30` | Max pages to parse |
| `PDF__MAX_SIZE_MB` | int | `20` | Max file size (MB) |
| `PDF__OCR` | bool | `false` | Enable OCR |
| `PDF__TABLE_EXTRACT` | bool | `true` | Extract table structure |

## Text Chunking

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `CHUNKING__SIZE` | int | `600` | Target chunk size (words) |
| `CHUNKING__OVERLAP` | int | `100` | Overlap between chunks |
| `CHUNKING__MIN_SIZE` | int | `100` | Min words per chunk |
| `CHUNKING__SECTION_AWARE` | bool | `true` | Respect section boundaries |

## Cache (Redis)

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `CACHE__HOST` | str | `localhost` | Redis host |
| `CACHE__PORT` | int | `6379` | Redis port |
| `CACHE__PASSWORD` | str | — | Redis password |
| `CACHE__DB` | int | `0` | Redis database number |
| `CACHE__TTL_HOURS` | int | `6` | Cache entry lifetime |

## Observability (Langfuse)

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `TRACING__ENABLED` | bool | `false` | Enable Langfuse tracing |
| `TRACING__HOST` | str | `http://localhost:3001` | Langfuse endpoint |
| `TRACING__PUBLIC_KEY` | str | — | Langfuse public key |
| `TRACING__SECRET_KEY` | str | — | Langfuse secret key |
| `TRACING__FLUSH_AT` | int | `15` | Batch size before flush |
| `TRACING__FLUSH_INTERVAL` | float | `1.0` | Flush interval (seconds) |

## Telegram Bot

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `TELEGRAM__ENABLED` | bool | `false` | Enable Telegram bot |
| `TELEGRAM__TOKEN` | str | — | Bot token from BotFather |
