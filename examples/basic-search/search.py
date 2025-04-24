"""Search for papers using the arxiv-sentinel API."""

import json
import sys

import httpx

API = "http://localhost:8000/api/v1"


def main() -> None:
    query = sys.argv[1] if len(sys.argv) > 1 else (
        "retrieval augmented generation"
    )
    resp = httpx.post(
        f"{API}/search",
        json={
            "query": query,
            "hybrid": True,
            "size": 5,
        },
        timeout=30.0,
    )
    resp.raise_for_status()
    data = resp.json()

    print(f"Query: {data['query']}")
    print(f"Mode:  {data['mode']}")
    print(f"Total: {data['total']}\n")

    for i, hit in enumerate(data["hits"], 1):
        print(f"{i}. [{hit['arxiv_id']}] {hit['title']}")
        print(f"   Score: {hit['score']:.3f}")
        print(f"   {hit['chunk_text'][:120]}...\n")


if __name__ == "__main__":
    main()
