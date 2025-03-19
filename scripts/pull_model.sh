#!/usr/bin/env bash
# Pull the default Ollama model into the running container.
set -euo pipefail

MODEL="${1:-llama3.2:1b}"
CONTAINER="${2:-sentinel-ollama}"

echo "Pulling ${MODEL} into ${CONTAINER}..."
docker exec "${CONTAINER}" ollama pull "${MODEL}"
echo "Done."
