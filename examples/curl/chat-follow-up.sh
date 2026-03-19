#!/usr/bin/env bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "go ahead",
    "response_mode": "code",
    "messages": [
      {
        "role": "user",
        "content": "Can you give me a sample Java web app?"
      },
      {
        "role": "assistant",
        "content": "I can give you a Java sample. Say go ahead if you want the code."
      }
    ]
  }'
