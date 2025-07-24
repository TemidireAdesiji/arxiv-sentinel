"""Fetch recent arXiv papers directly (no API required)."""

import asyncio

# Add the project src/ to the path if running standalone.
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root / "src"))

from sentinel.ingestion.arxiv import ArxivFetcher
from sentinel.settings import ArxivCfg


async def main() -> None:
    cfg = ArxivCfg(max_papers=5, category="cs.AI")
    fetcher = ArxivFetcher(cfg)
    try:
        papers = await fetcher.fetch_recent()
        for p in papers:
            print(f"[{p.arxiv_id}] {p.title}")
            print(
                f"  Authors: {', '.join(p.authors[:3])}"
            )
            print(f"  Categories: {p.categories}")
            print(f"  PDF: {p.pdf_link}\n")
    finally:
        await fetcher.close()


if __name__ == "__main__":
    asyncio.run(main())
