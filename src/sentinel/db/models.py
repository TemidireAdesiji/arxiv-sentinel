"""SQLAlchemy ORM models — single source of truth for schema."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Index,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
)


def _utcnow() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""


class PaperRow(Base):
    """Persisted arXiv paper with parsed content."""

    __tablename__ = "papers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    arxiv_id: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    authors: Mapped[list] = mapped_column(JSON, default=list)
    abstract: Mapped[str] = mapped_column(Text, default="")
    categories: Mapped[list] = mapped_column(JSON, default=list)
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    pdf_link: Mapped[str] = mapped_column(String(512), default="")

    body_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    sections: Mapped[list | None] = mapped_column(JSON, nullable=True)
    references: Mapped[list | None] = mapped_column(JSON, nullable=True)

    parser_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    parser_meta: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    pdf_parsed: Mapped[bool] = mapped_column(Boolean, default=False)
    parsed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,
        onupdate=_utcnow,
    )

    __table_args__ = (
        Index("ix_papers_arxiv_id", "arxiv_id"),
        Index("ix_papers_published", "published_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<PaperRow arxiv_id={self.arxiv_id!r} title={self.title[:40]!r}>"
        )
