# Contributing to arxiv-sentinel

Thanks for considering a contribution.  This document explains how to get started, what we expect from pull requests, and how to report issues.

## Getting Started

```bash
git clone https://github.com/user/arxiv-sentinel.git
cd arxiv-sentinel
uv sync --all-groups
pre-commit install
```

## Development Workflow

1. Create a feature branch from `main`:
   ```bash
   git checkout -b feat/your-feature
   ```
2. Make your changes.
3. Run the full quality pipeline:
   ```bash
   make format
   make lint
   make typecheck
   make test
   ```
4. Commit using [Conventional Commits](https://www.conventionalcommits.org/):
   ```
   feat: add multi-model support
   fix: handle empty search results gracefully
   docs: update configuration reference
   ```
5. Push and open a PR against `main`.

## Running Tests

```bash
# Unit + API tests (fast, no services)
make test

# With coverage
make test-cov

# Integration tests (requires Docker services)
make start
make test-int
```

## Code Style

- **Formatter**: Ruff (`ruff format`)
- **Linter**: Ruff (`ruff check`)
- **Type checker**: mypy
- **Line length**: 79 characters
- **Imports**: sorted by ruff with `isort` rules

Pre-commit hooks enforce all of the above automatically.

## Pull Request Process

1. Fork the repository and create a feature branch.
2. Write tests for every new behaviour.
3. Ensure all tests pass and coverage does not decrease.
4. Update documentation if your change affects the public API.
5. Submit a PR with a clear description of *what* and *why*.

## Reporting Issues

Please use [GitHub Issues](https://github.com/user/arxiv-sentinel/issues) with one of the provided templates:

- **Bug report**: include steps to reproduce, expected vs actual behaviour, and environment details.
- **Feature request**: describe the use-case and proposed solution.
