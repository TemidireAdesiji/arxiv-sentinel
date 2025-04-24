# Agentic Q&A Example

Demonstrates the agentic RAG endpoint that shows reasoning steps.

## Prerequisites

- arxiv-sentinel API running on `localhost:8000`
- Ollama model pulled (`llama3.2:1b`)
- At least one paper indexed

## Run

```bash
pip install httpx
python ask_agent.py "What are the latest advances in LLM reasoning?"
```
