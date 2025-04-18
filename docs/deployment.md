# Deployment Guide

## Docker Compose (recommended)

### Core Services Only

```bash
cp .env.example .env
# Edit .env with your JINA_API_KEY
docker compose up --build -d
docker exec sentinel-ollama ollama pull llama3.2:1b
```

This starts: API, PostgreSQL, OpenSearch, Redis, Ollama.

### With Observability (Langfuse)

```bash
docker compose -f compose.yml \
  -f compose.observability.yml up --build -d
```

Adds: Langfuse web + worker, Langfuse Postgres, Redis, MinIO, ClickHouse.

### With Ingestion Pipeline (Airflow)

```bash
docker compose -f compose.yml \
  -f compose.pipeline.yml up --build -d
```

Adds: Airflow webserver + scheduler.

### Full Stack

```bash
make start-all
```

## Service Ports

| Service | Port | Notes |
|---------|------|-------|
| API | 8000 | Swagger at `/docs` |
| PostgreSQL | 5432 | Main database |
| OpenSearch | 9200 | Search engine |
| OpenSearch Dashboards | 5601 | Visualisation |
| Redis | 6379 | Cache |
| Ollama | 11434 | LLM |
| Langfuse | 3001 | Tracing dashboard |
| Airflow | 8080 | DAG management |
| Gradio | 7861 | Web UI (run separately) |

## Running Gradio UI

The Gradio interface connects to the running API:

```bash
uv run python launch_ui.py
```

## Production Considerations

### Environment

Set `ENVIRONMENT=production` in `.env`.  This enables:
- JSON-formatted structured logs
- Stricter error reporting

### Secrets

Never commit `.env`.  Use a secrets manager in production:
- Docker secrets
- Kubernetes secrets
- AWS Secrets Manager / HashiCorp Vault

### Scaling

- **API**: Increase `--workers` in the Dockerfile CMD.
- **OpenSearch**: Move to a multi-node cluster.
- **Redis**: Use Redis Cluster for high availability.
- **Ollama**: Deploy on GPU-equipped nodes.

### Backups

- PostgreSQL: schedule `pg_dump` via cron.
- OpenSearch: use snapshot/restore API.
- Redis: AOF persistence is enabled by default.
