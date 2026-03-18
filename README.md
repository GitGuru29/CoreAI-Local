# CoreAI-Local

`CoreAI-Local` is a lightweight FastAPI gateway that exposes a clean local REST API on top of a locally running Ollama instance. It is designed for offline-first Linux setups where the AI model and server stay on the same machine, while other devices on a trusted LAN or hotspot can call the gateway without any cloud dependency.

The gateway connects only to Ollama's local API at `http://localhost:11434` by default and exposes:

- `GET /health`
- `GET /models`
- `POST /chat`

## Features

- Offline-first architecture for local and LAN-only usage
- FastAPI-based REST API with automatic OpenAPI docs
- Modular backend layout with separated routes, schemas, services, config, and utilities
- Graceful handling when Ollama is unavailable
- Basic structured logging for request tracing and troubleshooting
- `.env`-driven configuration for model selection, ports, and runtime settings

## Project Structure

```text
CoreAI-Local/
├── app/
│   ├── api/
│   │   ├── dependencies.py
│   │   ├── error_handlers.py
│   │   ├── router.py
│   │   └── routes/
│   │       ├── chat.py
│   │       ├── health.py
│   │       └── models.py
│   ├── core/
│   │   ├── config.py
│   │   ├── logging.py
│   │   └── middleware.py
│   ├── schemas/
│   │   ├── chat.py
│   │   ├── health.py
│   │   └── models.py
│   ├── services/
│   │   └── ollama.py
│   ├── utils/
│   │   └── errors.py
│   └── main.py
├── .env.example
├── .gitignore
├── README.md
└── requirements.txt
```

## Prerequisites

- Linux machine running Python 3.11+
- Ollama installed locally on the same Linux machine
- A model already available on disk, such as `qwen2.5-coder:7b`

Important: this gateway works fully offline once Ollama and the target model already exist on the host. If the model has not been downloaded yet, preload it before disconnecting from the internet, or transfer the local Ollama model data from another machine.

## Setup

Create a virtual environment and install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create your environment file:

```bash
cp .env.example .env
```

Default configuration:

```env
APP_NAME=CoreAI Local
APP_VERSION=0.1.0
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_TIMEOUT=60
DEFAULT_MODEL=qwen2.5-coder:7b
```

## Run Ollama Locally

Start Ollama on the Linux host:

```bash
ollama serve
```

Check locally available models:

```bash
ollama list
```

If you are still in an online setup phase and need the default model:

```bash
ollama pull qwen2.5-coder:7b
```

Once the model is available locally, the gateway can run without internet access.

## Start the API Server

Run the FastAPI server from the repository root:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The API will then be reachable from:

- The Linux host: `http://127.0.0.1:8000`
- Other devices on the same LAN or hotspot: `http://<linux-host-ip>:8000`

Example:

```bash
ip addr
```

Look for your local network IP such as `192.168.1.20`, then call the gateway from a Mac or another device with `http://192.168.1.20:8000`.

## API Endpoints

### `GET /health`

Returns gateway health and whether Ollama is reachable.

Example:

```bash
curl http://127.0.0.1:8000/health
```

Typical response when Ollama is running:

```json
{
  "status": "ok",
  "service": "CoreAI Local",
  "ollama_available": true,
  "default_model": "qwen2.5-coder:7b",
  "ollama_base_url": "http://localhost:11434",
  "available_models": 1,
  "detail": null
}
```

### `GET /models`

Lists the models currently available inside local Ollama storage.

```bash
curl http://127.0.0.1:8000/models
```

### `POST /chat`

Sends a prompt to Ollama and returns a generated response.

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Write a short Python function that reverses a string.",
    "model": "qwen2.5-coder:7b"
  }'
```

You can also omit `model` to use `DEFAULT_MODEL` from `.env`.

Example response:

```json
{
  "model": "qwen2.5-coder:7b",
  "response": "def reverse_string(value: str) -> str:\n    return value[::-1]",
  "done": true,
  "done_reason": "stop",
  "created_at": "2026-03-18T00:00:00Z",
  "total_duration": 123456789,
  "load_duration": 1234567,
  "prompt_eval_count": 12,
  "eval_count": 21,
  "prompt_eval_duration": 3456789,
  "eval_duration": 9876543
}
```

## OpenAPI Docs

When the server is running, interactive docs are available at:

- `http://127.0.0.1:8000/docs`
- `http://<linux-host-ip>:8000/docs`

## Operational Notes

- Keep Ollama bound locally. The FastAPI gateway is the component intended for LAN access.
- Use a trusted LAN or hotspot only. If the host firewall is enabled, allow port `8000` only on the private interface you intend to use.
- If Ollama is not running, `GET /health` will report a degraded state and `GET /models` or `POST /chat` will return a clear error response.

## Development

Basic syntax validation:

```bash
python3 -m compileall app
```

Run the included smoke tests:

```bash
python3 -m unittest discover -s tests
```

## License

Add your preferred license before publishing the repository.
