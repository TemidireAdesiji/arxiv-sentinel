"""Gradio web interface for interactive paper Q&A."""

from __future__ import annotations

import httpx

_API = "http://localhost:8000/api/v1"


def _ask(
    question: str,
    use_hybrid: bool,
    top_k: int,
) -> str:
    """Call the /ask endpoint and format the response."""
    payload = {
        "query": question,
        "hybrid": use_hybrid,
        "top_k": int(top_k),
    }
    try:
        resp = httpx.post(
            f"{_API}/ask",
            json=payload,
            timeout=120.0,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        return f"Error: {exc}"

    answer = data.get("answer", "")
    sources = data.get("sources", [])
    mode = data.get("mode", "")
    chunks = data.get("chunks_used", 0)

    parts = [
        answer,
        "",
        f"---  \n*Mode: {mode} | Chunks: {chunks}*",
    ]
    if sources:
        parts.append("\n**Sources:**")
        for s in sources:
            parts.append(f"- {s}")
    return "\n".join(parts)


def _ask_agentic(question: str) -> str:
    """Call the /ask-agentic endpoint."""
    payload = {"query": question}
    try:
        resp = httpx.post(
            f"{_API}/ask-agentic",
            json=payload,
            timeout=180.0,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        return f"Error: {exc}"

    answer = data.get("answer", "")
    steps = data.get("reasoning_steps", [])
    sources = data.get("sources", [])

    parts = [answer, "", "**Reasoning:**"]
    for i, s in enumerate(steps, 1):
        parts.append(f"{i}. {s}")
    if sources:
        parts.append("\n**Sources:**")
        for s in sources:
            parts.append(f"- {s}")
    return "\n".join(parts)


def launch() -> None:
    """Build and start the Gradio interface."""
    import gradio as gr

    with gr.Blocks(
        title="arxiv-sentinel",
        theme=gr.themes.Soft(),
    ) as demo:
        gr.Markdown(
            "# arxiv-sentinel\nAsk questions about recent AI research."
        )

        with gr.Tab("Standard RAG"):
            q1 = gr.Textbox(
                label="Question",
                placeholder="What are recent advances in…",
            )
            with gr.Row():
                hybrid = gr.Checkbox(
                    label="Hybrid search",
                    value=True,
                )
                topk = gr.Slider(
                    1,
                    10,
                    value=3,
                    step=1,
                    label="Top K",
                )
            btn1 = gr.Button("Ask")
            out1 = gr.Markdown()
            btn1.click(_ask, [q1, hybrid, topk], out1)

        with gr.Tab("Agentic RAG"):
            q2 = gr.Textbox(
                label="Question",
                placeholder="Explain how…",
            )
            btn2 = gr.Button("Ask (Agentic)")
            out2 = gr.Markdown()
            btn2.click(_ask_agentic, [q2], out2)

    demo.launch(
        server_name="0.0.0.0",
        server_port=7861,
    )


if __name__ == "__main__":
    launch()
