#!/usr/bin/env bash
curl -N -X POST http://127.0.0.1:8000/chat/stream \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Explain what FastAPI dependencies are in two short sentences.",
    "model": "llama3.2:latest"
  }'
