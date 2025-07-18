# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [0.1.0] - 2025-06-01

### Added
- Hybrid search (BM25 + vector) via OpenSearch with native RRF pipeline.
- Standard RAG question-answering endpoint with streaming support.
- Agentic RAG pipeline with guardrails, relevance grading, and query rewriting.
- arXiv paper ingestion with Docling PDF parsing and section-aware chunking.
- Jina AI embedding generation (v3 model, 1024 dimensions).
- Ollama local LLM inference integration.
- Redis exact-match response caching with configurable TTL.
- Langfuse end-to-end request tracing and user-feedback collection.
- Airflow DAG for scheduled weekday paper ingestion.
- Telegram bot interface for conversational paper Q&A.
- Gradio web UI for interactive exploration.
- Per-service health check endpoint.
- Docker Compose orchestration with split profiles (core, observability, pipeline).
- Comprehensive test suite (unit, API, integration).
- CI workflow with lint, type-check, and test stages.
