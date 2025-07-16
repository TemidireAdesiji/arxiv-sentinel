# Troubleshooting

## Common Issues

### API returns "degraded" health status

Check which service is unhealthy:

```bash
curl http://localhost:8000/api/v1/health | python3 -m json.tool
```

Then verify the specific service:

```bash
# Database
docker exec sentinel-postgres pg_isready -U sentinel

# OpenSearch
curl http://localhost:9200/_cluster/health

# Ollama
curl http://localhost:11434/api/version
```

### OpenSearch index not created

The API creates the index on startup.  If it fails:

```bash
# Check OpenSearch logs
docker logs sentinel-opensearch

# Manually verify
curl http://localhost:9200/_cat/indices
```

Common cause: OpenSearch not ready when API starts.  Restart the API:

```bash
docker restart sentinel-api
```

### Ollama model not found

The model must be pulled manually after first start:

```bash
docker exec sentinel-ollama ollama pull llama3.2:1b
```

### Search returns no results

1. Check if papers have been ingested:
   ```bash
   curl http://localhost:9200/arxiv-papers-chunks/_count
   ```
2. If count is 0, run the ingestion pipeline or trigger it via Airflow.

### Redis connection refused

Verify Redis is running:

```bash
docker exec sentinel-redis redis-cli ping
```

If Redis is down, the API will still work — caching is optional.

### Jina API errors

- Verify your API key: `echo $JINA_API_KEY`
- Check Jina API status at https://status.jina.ai
- If the key is invalid, the API falls back to BM25-only search.

### Port conflicts

If a port is already in use, change it in `compose.yml`:

```yaml
ports:
  - "8001:8000"  # Map to a different host port
```

### Memory issues with OpenSearch

Increase the JVM heap in `compose.yml`:

```yaml
environment:
  OPENSEARCH_JAVA_OPTS: "-Xms1g -Xmx1g"
```

## Getting Help

If none of the above resolves your issue, please [open a GitHub issue](https://github.com/user/arxiv-sentinel/issues) with:

1. The output of `docker compose ps`
2. Relevant service logs (`docker logs <container>`)
3. Your OS and Docker version
