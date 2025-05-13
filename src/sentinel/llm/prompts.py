"""Prompt templates for RAG and agentic reasoning."""

from __future__ import annotations

SYSTEM_ACADEMIC = (
    "You are a research assistant specialising in "
    "computer-science and artificial-intelligence papers "
    "from arXiv.  Answer questions using ONLY the "
    "provided context.  If the context does not contain "
    "enough information, say so honestly.  Cite paper "
    "titles when possible."
)

RAG_USER_TEMPLATE = (
    "Context (retrieved paper excerpts):\n"
    "---\n{context}\n---\n\n"
    "Question: {question}\n\n"
    "Provide a clear, well-structured answer."
)

GUARDRAIL_TEMPLATE = (
    "Evaluate whether the following query is about "
    "computer-science or AI research papers.  Return a "
    "JSON object with a single key 'score' whose value "
    "is an integer from 0 (completely off-topic) to 100 "
    "(clearly about CS/AI research).\n\n"
    "Query: {query}\n\n"
    "JSON:"
)

GRADING_TEMPLATE = (
    "You are a relevance grader.  Given a user question "
    "and a retrieved document excerpt, decide whether the "
    "document is relevant.  Return a JSON object with a "
    "single key 'relevant' whose value is either "
    "'yes' or 'no'.\n\n"
    "Question: {question}\n"
    "Document: {document}\n\n"
    "JSON:"
)

REWRITE_TEMPLATE = (
    "The following search query did not return useful "
    "results.  Rewrite it to improve retrieval.  Return "
    "ONLY the improved query, nothing else.\n\n"
    "Original query: {query}\n\n"
    "Improved query:"
)


def build_rag_prompt(
    question: str,
    chunks: list[str],
) -> str:
    """Assemble the user prompt for answer generation."""
    context = "\n\n".join(f"[{i + 1}] {c}" for i, c in enumerate(chunks))
    return RAG_USER_TEMPLATE.format(context=context, question=question)
