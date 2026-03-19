# CoreAI-Local

`CoreAI-Local` is an offline-first FastAPI gateway for a locally running Ollama instance on Linux. It exposes a clean REST API that stays on the local machine and local network, making it useful as a lightweight AI backend for other LAN clients such as a Mac app, a browser UI, or a mobile client.

The gateway talks to Ollama only through its local API at `http://localhost:11434` and is designed to keep working without internet once Ollama and the target models already exist on disk.

## What it provides

- `GET /health`
- `GET /info`
- `GET /models`
- `POST /chat`
- `POST /chat/stream`
- `POST /summarize`
- `POST /analyze-code`

## Current backend features

- Offline-first Linux deployment with LAN access
- Optional model selection per request
- Streaming chat responses with server-sent events
- Optional API-key auth for LAN clients
- Structured JSON errors with readable status codes
- Installed-model validation before generation
- Request timing logs with client IP and selected model
- File logging to `logs/server.log`
- Local request guard with rate limiting and queue protection
- Summarization and code-analysis endpoints
- Reverse-proxy support with HTTPS-ready deployment files
- `.env`-driven runtime config
- Example `curl` scripts in `examples/curl/`
- `systemd` unit files in `deploy/systemd/`

## Project structure

```text
CoreAI-Local/
├── app/
│   ├── api/
│   │   ├── dependencies.py
│   │   ├── error_handlers.py
│   │   ├── router.py
│   │   └── routes/
│   │       ├── analyze_code.py
│   │       ├── chat.py
│   │       ├── health.py
│   │       ├── info.py
│   │       ├── models.py
│   │       └── summarize.py
│   ├── core/
│   │   ├── config.py
│   │   ├── logging.py
│   │   └── middleware.py
│   ├── schemas/
│   │   ├── analyze_code.py
│   │   ├── chat.py
│   │   ├── health.py
│   │   ├── info.py
│   │   ├── models.py
│   │   └── summarize.py
│   ├── services/
│   │   ├── ollama.py
│   │   ├── request_guard.py
│   │   └── task_prompts.py
│   ├── utils/
│   │   ├── errors.py
│   │   └── guards.py
│   └── main.py
├── deploy/systemd/
├── examples/curl/
├── logs/
├── tests/
├── .env.example
├── requirements.txt
└── README.md
```

## Requirements

- Linux host
- Python 3.11+
- Ollama installed locally
- One or more models already present locally, for example:
  - `qwen2.5-coder:7b`
  - `llama3.2:latest`

Important: if the models are not already local, you must preload them before going offline.

## Setup

Create a virtual environment and install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create your local environment file:

```bash
cp .env.example .env
```

Default configuration:

```env
APP_NAME=CoreAI Local
APP_VERSION=0.1.0
APP_ENV=development
SERVER_MODE=offline-local
API_HOST=0.0.0.0
API_PORT=8000
AUTH_ENABLED=false
AUTH_API_KEY=
AUTH_EXEMPT_PATHS=/health,/info,/docs,/openapi.json,/redoc
LOG_LEVEL=INFO
LOG_DIR=logs
LOG_FILE=server.log
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_TIMEOUT=60
DEFAULT_MODEL=qwen2.5-coder:7b
MAX_PROMPT_CHARS=12000
MAX_TEXT_CHARS=24000
MAX_CODE_CHARS=32000
MAX_TASK_CHARS=1000
RATE_LIMIT_REQUESTS=30
RATE_LIMIT_WINDOW_SECONDS=60
MAX_CONCURRENT_AI_REQUESTS=2
QUEUE_WAIT_TIMEOUT=5
CORS_ALLOWED_ORIGINS=
```

## Start Ollama

Run Ollama locally:

```bash
ollama serve
```

Check installed models:

```bash
ollama list
```

If you are still in the online setup phase and need a model:

```bash
ollama pull qwen2.5-coder:7b
ollama pull llama3.2:latest
```

## Optional auth layer

`CoreAI-Local` supports a small API-key auth layer intended for trusted LAN use.

Enable it in `.env`:

```env
AUTH_ENABLED=true
AUTH_API_KEY=replace-with-a-long-local-secret
AUTH_EXEMPT_PATHS=/health,/info,/docs,/openapi.json,/redoc
```

Accepted request headers:

- `X-API-Key: <your-secret>`
- `Authorization: Bearer <your-secret>`

By default:

- `GET /health` stays public
- `GET /info` stays public
- model and generation endpoints require the key when auth is enabled

Example:

```bash
curl http://127.0.0.1:8000/models \
  -H "X-API-Key: replace-with-a-long-local-secret"
```

## Start the API gateway

From the repository root:

```bash
source .venv/bin/activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Available URLs:

- local host: `http://127.0.0.1:8000`
- LAN / hotspot: `http://<linux-ip>:8000`
- docs: `http://127.0.0.1:8000/docs`

Example to find the Linux IP:

```bash
ip -4 addr show
```

## Endpoints

### `GET /health`

Returns service health plus Ollama status, version, default model information, and the locally available model list.

```bash
curl http://127.0.0.1:8000/health
```

### `GET /info`

Returns server metadata, enabled capabilities, and auth state.

```bash
curl http://127.0.0.1:8000/info
```

### `GET /models`

Returns the locally installed Ollama models.

```bash
curl http://127.0.0.1:8000/models
```

### `POST /chat`

Send a prompt and receive the full response when generation completes.

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Explain what FastAPI dependencies do.",
    "model": "qwen2.5-coder:7b"
  }'
```

### `POST /chat/stream`

Stream the response as server-sent events:

```bash
curl -N -X POST http://127.0.0.1:8000/chat/stream \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Explain what FastAPI dependencies are in two short sentences.",
    "model": "llama3.2:latest"
  }'
```

Example event:

```text
data: {"model":"llama3.2:latest","chunk":"FastAPI dependencies...","done":false}
```

### `POST /summarize`

Summarize longer text with an optional style.

```bash
curl -X POST http://127.0.0.1:8000/summarize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "CoreAI-Local is an offline FastAPI gateway for Ollama running on Linux.",
    "style": "brief",
    "model": "llama3.2:latest"
  }'
```

### `POST /analyze-code`

Analyze code for explanation, review, bug-finding, cleanup, documentation, or optimization.

```bash
curl -X POST http://127.0.0.1:8000/analyze-code \
  -H "Content-Type: application/json" \
  -d '{
    "code": "fun main() { println(\"Hi\") }",
    "language": "kotlin",
    "task": "explain",
    "model": "llama3.2:latest"
  }'
```

## Error handling

The API returns structured errors such as:

```json
{
  "error": "Requested model is not installed.",
  "code": "model_not_installed",
  "details": {
    "model": "missing:model",
    "available_models": [
      "qwen2.5-coder:7b",
      "llama3.2:latest"
    ]
  }
}
```

Authentication failures return:

```json
{
  "error": "Valid API key required.",
  "code": "authentication_failed",
  "details": {
    "accepted_headers": [
      "X-API-Key",
      "Authorization: Bearer <token>"
    ]
  }
}
```

Common cases handled:

- Ollama unavailable
- model not installed
- timeout while generating
- authentication missing or invalid
- invalid payload JSON
- validation errors
- request size too large
- local queue full
- rate-limited client

## Logs

Console logs are emitted while the server is running, and persistent logs are written to:

```text
logs/server.log
```

These logs include:

- client IP
- endpoint path
- selected model
- status code
- request duration

## Examples

Example `curl` scripts are included in:

```text
examples/curl/
```

Current scripts:

- `health.sh`
- `info.sh`
- `models.sh`
- `chat.sh`
- `chat-stream.sh`
- `summarize.sh`
- `analyze-code.sh`

## systemd auto-start

Sample service files are included in:

```text
deploy/systemd/
```

Install them:

```bash
sudo cp deploy/systemd/ollama-local.service /etc/systemd/system/
sudo cp deploy/systemd/coreai-local.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now ollama-local.service
sudo systemctl enable --now coreai-local.service
```

Check status:

```bash
sudo systemctl status ollama-local.service
sudo systemctl status coreai-local.service
```

Important: the included unit files are currently configured for this repository path and user. If you move the project, update the unit files before installing them.

The included `coreai-local.service` binds Uvicorn to `127.0.0.1:8000` so it can sit safely behind a reverse proxy.

The included `ollama-local.service` also sets `OLLAMA_MODELS=/var/lib/ollama` so the service can reuse models already pulled into the local system store. If your machine stores models somewhere else, update that path before installing or restarting the unit.

## HTTPS reverse proxy

This repository includes an `nginx` deployment config in:

```text
deploy/nginx/
```

Recommended host layout:

- `CoreAI-Local` on `127.0.0.1:8000`
- `nginx` on `443` with TLS
- optional `80 -> 443` redirect

The provided config is set up for:

- `localhost`
- `127.0.0.1`
- current LAN IP `10.113.228.6`

Install nginx and the reverse proxy with:

```bash
sudo pacman -S --needed --noconfirm nginx
sudo bash deploy/nginx/install-nginx.sh 10.113.228.6
```

The installer patches `/etc/nginx/nginx.conf` to include `/etc/nginx/conf.d/*.conf` when needed. This matters on hosts where nginx is installed with only the default welcome site active.

If your LAN IP changes later, rerun:

```bash
sudo bash deploy/nginx/install-nginx.sh <new-lan-ip>
```

Example protected request through HTTPS:

```bash
curl https://10.113.228.6/models \
  --insecure \
  -H "X-API-Key: replace-with-your-secret"
```

`--insecure` is only needed until the self-signed certificate is trusted by the client machine.

## Development

Basic syntax validation:

```bash
python3 -m compileall app
```

Unit tests:

```bash
python3 -m unittest discover -s tests
```

## Security notes

- Keep Ollama bound locally.
- Expose the FastAPI gateway only on a trusted LAN or hotspot.
- Leave `CORS_ALLOWED_ORIGINS` empty unless you actually need browser-based access.
- Use private network firewall rules if other devices will connect.

## License

This repository includes a license file at the root.
