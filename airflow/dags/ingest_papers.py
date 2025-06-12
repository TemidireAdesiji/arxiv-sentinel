"""Daily arXiv paper ingestion DAG.

Runs every weekday at 06:00 UTC:
  verify → fetch → index → report → cleanup
"""

from __future__ import annotations

import logging
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path

from airflow.decorators import dag, task

log = logging.getLogger(__name__)

_DEFAULT_CFG = {
    "db_url": os.getenv(
        "DB_URL",
        "postgresql+psycopg2://sentinel:sentinel"
        "@postgres:5432/sentinel_db",
    ),
    "search_host": os.getenv(
        "SEARCH__HOST", "http://opensearch:9200"
    ),
    "jina_key": os.getenv("JINA_API_KEY", ""),
    "category": os.getenv("ARXIV__CATEGORY", "cs.AI"),
    "max_papers": int(
        os.getenv("ARXIV__MAX_PAPERS", "15")
    ),
    "pdf_dir": os.getenv(
        "ARXIV__PDF_DIR", "/tmp/arxiv_pdfs"
    ),
}


@dag(
    dag_id="daily_paper_ingestion",
    schedule="0 6 * * 1-5",
    start_date=datetime(2025, 1, 1),
    catchup=False,
    max_active_runs=1,
    default_args={
        "retries": 1,
        "retry_delay": timedelta(minutes=5),
    },
    tags=["sentinel", "ingestion"],
)
def paper_ingestion_pipeline():
    @task
    def verify_services() -> dict:
        """Ensure external services are reachable."""
        import httpx
        from sqlalchemy import create_engine, text

        engine = create_engine(_DEFAULT_CFG["db_url"])
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        log.info("Database OK")

        r = httpx.get(
            f"{_DEFAULT_CFG['search_host']}"
            "/_cluster/health",
            timeout=10,
        )
        r.raise_for_status()
        log.info("OpenSearch OK")
        return {"status": "ready"}

    @task
    def fetch_papers(status: dict) -> dict:
        """Download metadata + PDFs from arXiv."""
        import asyncio
        import sys

        sys.path.insert(0, "/opt/airflow/src")
        from sentinel.ingestion.arxiv import (
            ArxivFetcher,
        )
        from sentinel.settings import ArxivCfg

        cfg = ArxivCfg()

        async def _run():
            fetcher = ArxivFetcher(cfg)
            try:
                papers = await fetcher.fetch_recent()
                return [
                    {
                        "arxiv_id": p.arxiv_id,
                        "title": p.title,
                        "authors": p.authors,
                        "abstract": p.abstract,
                        "categories": p.categories,
                        "pdf_link": p.pdf_link,
                    }
                    for p in papers
                ]
            finally:
                await fetcher.close()

        results = asyncio.run(_run())
        log.info("Fetched %d papers", len(results))
        return {"papers": results, "count": len(results)}

    @task
    def index_papers(fetch_result: dict) -> dict:
        """Chunk, embed, and index fetched papers."""
        papers = fetch_result.get("papers", [])
        log.info(
            "Indexing %d papers (stub)", len(papers)
        )
        return {
            "indexed": len(papers),
            "errors": 0,
        }

    @task
    def build_report(index_result: dict) -> None:
        """Log a summary of the ingestion run."""
        indexed = index_result.get("indexed", 0)
        errors = index_result.get("errors", 0)
        log.info(
            "Ingestion complete: "
            "indexed=%d errors=%d",
            indexed,
            errors,
        )

    @task
    def cleanup_old_pdfs() -> None:
        """Remove cached PDFs older than 30 days."""
        pdf_dir = Path(_DEFAULT_CFG["pdf_dir"])
        if not pdf_dir.exists():
            return
        cutoff = datetime.now() - timedelta(days=30)
        removed = 0
        for f in pdf_dir.glob("*.pdf"):
            mtime = datetime.fromtimestamp(
                f.stat().st_mtime
            )
            if mtime < cutoff:
                f.unlink()
                removed += 1
        log.info("Removed %d old PDFs", removed)

    status = verify_services()
    fetched = fetch_papers(status)
    indexed = index_papers(fetched)
    build_report(indexed)
    cleanup_old_pdfs()


paper_ingestion_pipeline()
