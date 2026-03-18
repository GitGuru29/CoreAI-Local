#!/usr/bin/env bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Explain what a FastAPI dependency does.",
    "model": "qwen2.5-coder:7b"
  }'
