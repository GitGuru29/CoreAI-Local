#!/usr/bin/env bash
curl -N -X POST http://127.0.0.1:8000/summarize/stream \
  -H "Content-Type: application/json" \
  -d '{
    "text": "CoreAI-Local is an offline FastAPI gateway for Ollama running on Linux.",
    "style": "brief",
    "model": "llama3.2:latest"
  }'
