"""Ask a research question using the agentic pipeline."""

import sys

import httpx

API = "http://localhost:8000/api/v1"


def main() -> None:
    query = sys.argv[1] if len(sys.argv) > 1 else (
        "How do vision transformers work?"
    )
    print(f"Question: {query}\n")

    resp = httpx.post(
        f"{API}/ask-agentic",
        json={"query": query},
        timeout=180.0,
    )
    resp.raise_for_status()
    data = resp.json()

    print("Reasoning:")
    for i, step in enumerate(
        data["reasoning_steps"], 1
    ):
        print(f"  {i}. {step}")

    print(f"\nAnswer:\n{data['answer']}\n")

    if data["sources"]:
        print("Sources:")
        for src in data["sources"]:
            print(f"  - {src}")

    print(
        f"\nRetrieval attempts: "
        f"{data['retrieval_attempts']}"
    )
    if data.get("trace_id"):
        print(f"Trace ID: {data['trace_id']}")


if __name__ == "__main__":
    main()
