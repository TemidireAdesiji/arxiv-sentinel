"""Pydantic request / response models for every route."""

from __future__ import annotations

from pydantic import BaseModel, Field

# ── Health ───────────────────────────────────────────


class ServiceInfo(BaseModel):
    status: str
    message: str = ""


class HealthPayload(BaseModel):
    status: str
    version: str
    environment: str
    service_name: str
    services: dict[str, ServiceInfo] = Field(default_factory=dict)


# ── Search ───────────────────────────────────────────


class SearchBody(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    size: int = Field(default=10, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    hybrid: bool = True
    categories: list[str] | None = None
    latest_only: bool = False
    min_score: float | None = None


class HitItem(BaseModel):
    arxiv_id: str
    title: str = ""
    authors: list[str] = Field(default_factory=list)
    abstract: str = ""
    score: float = 0.0
    chunk_text: str = ""


class SearchPayload(BaseModel):
    query: str
    mode: str
    total: int
    hits: list[HitItem]


# ── Ask (RAG) ───────────────────────────────────────


class QuestionBody(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    top_k: int = Field(default=3, ge=1, le=10)
    hybrid: bool = True
    model: str = "llama3.2:1b"
    categories: list[str] | None = None


class AnswerPayload(BaseModel):
    query: str
    answer: str
    sources: list[str]
    chunks_used: int
    mode: str
    trace_id: str | None = None


# ── Agentic Ask ─────────────────────────────────────


class AgenticPayload(BaseModel):
    query: str
    answer: str
    sources: list[str]
    reasoning_steps: list[str]
    retrieval_attempts: int
    trace_id: str | None = None


# ── Feedback ─────────────────────────────────────────


class FeedbackBody(BaseModel):
    trace_id: str = Field(..., min_length=1)
    score: float = Field(..., ge=0.0, le=1.0)
    comment: str = ""


class FeedbackPayload(BaseModel):
    success: bool
