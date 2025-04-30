"""arXiv Atom-feed client for paper discovery."""

from __future__ import annotations

import asyncio
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

import httpx
import structlog

from sentinel.domain.paper import PaperRecord
from sentinel.exceptions import (
    ArxivApiError,
    ArxivRateLimited,
    ArxivTimeout,
    PdfDownloadError,
    PdfDownloadTimeout,
)
from sentinel.settings import ArxivCfg

log = structlog.get_logger(__name__)

_NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "arxiv": "http://arxiv.org/schemas/atom",
    "os": "http://a9.com/-/spec/opensearch/1.1/",
}


class ArxivFetcher:
    """Discover and download papers from the arXiv API."""

    def __init__(self, cfg: ArxivCfg) -> None:
        self._cfg = cfg
        self._http = httpx.AsyncClient(
            timeout=httpx.Timeout(float(cfg.timeout)),
        )

    async def fetch_recent(
        self,
        *,
        category: str | None = None,
        max_results: int | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> list[PaperRecord]:
        """Fetch recent papers for *category*."""
        cat = category or self._cfg.category
        limit = max_results or self._cfg.max_papers

        query = f"cat:{cat}"
        if date_from and date_to:
            query += f"+AND+submittedDate:[{date_from}+TO+{date_to}]"

        params: dict[str, str | int] = {
            "search_query": query,
            "start": 0,
            "max_results": limit,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        }

        try:
            resp = await self._http.get(self._cfg.api_url, params=params)
            resp.raise_for_status()
        except httpx.ReadTimeout as exc:
            raise ArxivTimeout(str(exc)) from exc
        except httpx.HTTPStatusError as exc:
            code = exc.response.status_code
            if code == 429:
                raise ArxivRateLimited("arXiv rate limit hit") from exc
            raise ArxivApiError(f"HTTP {code}") from exc
        except httpx.RequestError as exc:
            raise ArxivApiError(str(exc)) from exc

        papers = self._parse_feed(resp.text)
        log.info(
            "arxiv_fetched",
            category=cat,
            count=len(papers),
        )

        await asyncio.sleep(self._cfg.rate_delay)
        return papers

    async def download_pdf(
        self,
        pdf_url: str,
        dest: Path,
    ) -> Path:
        """Stream-download a PDF to *dest*."""
        dest.parent.mkdir(parents=True, exist_ok=True)
        for attempt in range(1, self._cfg.retries + 1):
            try:
                async with self._http.stream("GET", pdf_url) as r:
                    r.raise_for_status()
                    with dest.open("wb") as fp:
                        async for chunk in r.aiter_bytes(8192):
                            fp.write(chunk)
                log.info("pdf_downloaded", path=str(dest))
                return dest
            except httpx.ReadTimeout as exc:
                if attempt == self._cfg.retries:
                    raise PdfDownloadTimeout(str(exc)) from exc
            except httpx.RequestError as exc:
                if attempt == self._cfg.retries:
                    raise PdfDownloadError(str(exc)) from exc
            delay = self._cfg.retry_base * attempt
            await asyncio.sleep(delay)
        raise PdfDownloadError("Exhausted retries")

    async def close(self) -> None:
        await self._http.aclose()

    # -- XML parsing ----------------------------------------------

    @staticmethod
    def _parse_feed(xml_text: str) -> list[PaperRecord]:
        root = ET.fromstring(xml_text)
        papers: list[PaperRecord] = []
        for entry in root.findall("atom:entry", _NS):
            papers.append(ArxivFetcher._entry_to_record(entry))
        return papers

    @staticmethod
    def _entry_to_record(
        entry: ET.Element,
    ) -> PaperRecord:
        def _text(tag: str) -> str:
            el = entry.find(f"atom:{tag}", _NS)
            return (el.text or "").strip() if el is not None else ""

        arxiv_id = _text("id").split("/abs/")[-1]
        title = " ".join(_text("title").split())
        abstract = " ".join(_text("summary").split())

        authors = []
        for a in entry.findall("atom:author", _NS):
            name_el = a.find("atom:name", _NS)
            if name_el is not None:
                authors.append((name_el.text or "").strip())
        categories = [
            c.get("term", "")
            for c in entry.findall("atom:category", _NS)
            if c.get("term")
        ]
        pdf_link = ""
        for link in entry.findall("atom:link", _NS):
            if link.get("title") == "pdf":
                pdf_link = link.get("href", "")
                break

        pub_str = _text("published")
        published: datetime | None = None
        if pub_str:
            try:
                published = datetime.fromisoformat(
                    pub_str.replace("Z", "+00:00")
                )
            except ValueError:
                pass

        return PaperRecord(
            arxiv_id=arxiv_id,
            title=title,
            authors=authors,
            abstract=abstract,
            categories=categories,
            published=published,
            pdf_link=pdf_link,
        )


def create_arxiv_fetcher(
    cfg: ArxivCfg,
) -> ArxivFetcher:
    """Factory: build an ``ArxivFetcher``."""
    return ArxivFetcher(cfg)
