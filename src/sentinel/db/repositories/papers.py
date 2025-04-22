"""CRUD operations for the ``papers`` table."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import structlog
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_upsert

from sentinel.db.models import PaperRow
from sentinel.exceptions import RecordNotFound, RecordNotSaved

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

log = structlog.get_logger(__name__)


class PaperStore:
    """Repository for paper persistence operations."""

    def __init__(self, session: Session) -> None:
        self._s = session

    # -- reads ----------------------------------------------------

    def find_by_arxiv_id(self, arxiv_id: str) -> PaperRow:
        """Fetch one paper or raise ``RecordNotFound``."""
        row = self._s.execute(
            select(PaperRow).where(PaperRow.arxiv_id == arxiv_id)
        ).scalar_one_or_none()
        if row is None:
            raise RecordNotFound("Paper", arxiv_id)
        return row

    def exists(self, arxiv_id: str) -> bool:
        """Return *True* if the paper is already stored."""
        return (
            self._s.execute(
                select(PaperRow.id).where(PaperRow.arxiv_id == arxiv_id)
            ).scalar_one_or_none()
            is not None
        )

    def list_all(
        self,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[PaperRow]:
        """Return papers ordered by publish date (newest first)."""
        stmt = (
            select(PaperRow)
            .order_by(PaperRow.published_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return self._s.execute(stmt).scalars().all()

    def list_unparsed(self) -> Sequence[PaperRow]:
        """Return papers whose PDF has not been processed."""
        stmt = select(PaperRow).where(PaperRow.pdf_parsed.is_(False))
        return self._s.execute(stmt).scalars().all()

    # -- writes ---------------------------------------------------

    def add(self, row: PaperRow) -> PaperRow:
        """Insert a new paper row."""
        try:
            self._s.add(row)
            self._s.flush()
            return row
        except Exception as exc:
            self._s.rollback()
            raise RecordNotSaved(str(exc)) from exc

    def upsert(self, row: PaperRow) -> PaperRow:
        """Insert or update on ``arxiv_id`` conflict."""
        values = {
            c.name: getattr(row, c.name)
            for c in PaperRow.__table__.columns
            if c.name != "id"
        }
        stmt = (
            pg_upsert(PaperRow)
            .values(**values)
            .on_conflict_do_update(
                index_elements=["arxiv_id"],
                set_=values,
            )
        )
        self._s.execute(stmt)
        self._s.flush()
        return self.find_by_arxiv_id(row.arxiv_id)

    def mark_parsed(
        self,
        arxiv_id: str,
        body: str,
        sections: list[dict[str, str]] | None,
        parser: str,
    ) -> PaperRow:
        """Flag a paper as successfully parsed."""
        row = self.find_by_arxiv_id(arxiv_id)
        row.body_text = body
        row.sections = sections
        row.parser_name = parser
        row.pdf_parsed = True
        row.parsed_at = datetime.now(UTC)
        self._s.flush()
        return row

    # -- stats ----------------------------------------------------

    def count_total(self) -> int:
        """Total papers in the database."""
        from sqlalchemy import func

        result = self._s.execute(select(func.count(PaperRow.id)))
        return result.scalar_one()

    def count_parsed(self) -> int:
        """Papers whose PDF has been processed."""
        from sqlalchemy import func

        result = self._s.execute(
            select(func.count(PaperRow.id)).where(
                PaperRow.pdf_parsed.is_(True)
            )
        )
        return result.scalar_one()
