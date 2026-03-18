#!/usr/bin/env bash
curl -X POST http://127.0.0.1:8000/analyze-code \
  -H "Content-Type: application/json" \
  -d '{
    "code": "fun main() { println(\"Hi\") }",
    "language": "kotlin",
    "task": "explain",
    "model": "llama3.2:latest"
  }'
