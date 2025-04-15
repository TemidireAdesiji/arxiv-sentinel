.PHONY: help start stop restart status logs health \
       setup format lint typecheck test test-cov clean

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*##' $(MAKEFILE_LIST) \
	  | awk 'BEGIN {FS = ":.*## "}; {printf "  %-14s %s\n", $$1, $$2}'

# ── Service management ──────────────────────

start: ## Launch all services via Docker Compose
	docker compose up --build -d

start-obs: ## Launch with observability stack
	docker compose -f compose.yml \
	  -f compose.observability.yml up --build -d

start-all: ## Launch everything (core + obs + pipeline)
	docker compose -f compose.yml \
	  -f compose.observability.yml \
	  -f compose.pipeline.yml up --build -d

stop: ## Stop all running services
	docker compose -f compose.yml \
	  -f compose.observability.yml \
	  -f compose.pipeline.yml down

restart: ## Restart all running services
	docker compose restart

status: ## Show service status
	docker compose ps

logs: ## Tail service logs
	docker compose logs -f

health: ## Run health checks against all services
	@echo "=== API ==="
	@curl -sf http://localhost:8000/api/v1/health | python3 -m json.tool || echo "UNREACHABLE"
	@echo "\n=== OpenSearch ==="
	@curl -sf http://localhost:9200/_cluster/health | python3 -m json.tool || echo "UNREACHABLE"
	@echo "\n=== Ollama ==="
	@curl -sf http://localhost:11434/api/version | python3 -m json.tool || echo "UNREACHABLE"

# ── Development ─────────────────────────────

setup: ## Install dependencies with uv
	uv sync --all-groups

format: ## Format code with ruff
	uv run ruff format src/ tests/

lint: ## Lint code with ruff
	uv run ruff check --fix src/ tests/

typecheck: ## Run mypy type checks
	uv run mypy src/sentinel/

test: ## Run unit and API tests
	uv run pytest -x -q

test-cov: ## Run tests with coverage report
	uv run pytest --cov=sentinel --cov-report=html --cov-report=term

test-int: ## Run integration tests (requires services)
	uv run pytest -m integration -x -q

# ── Cleanup ─────────────────────────────────

clean: ## Remove containers, volumes, caches
	docker compose -f compose.yml \
	  -f compose.observability.yml \
	  -f compose.pipeline.yml down -v
	docker system prune -f
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage
