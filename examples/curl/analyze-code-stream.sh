#!/usr/bin/env bash
curl -N -X POST http://127.0.0.1:8000/analyze-code/stream \
  -H "Content-Type: application/json" \
  -d '{
    "code": "fun main() { println(\"Hi\") }",
    "language": "kotlin",
    "task": "review",
    "model": "llama3.2:latest"
  }'
