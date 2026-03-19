import json
import os
import socket
import subprocess
import threading
import time
import unittest
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON_BIN = REPO_ROOT / ".venv" / "bin" / "python"

AVAILABLE_MODELS = [
    {
        "name": "qwen2.5-coder:7b",
        "model": "qwen2.5-coder:7b",
        "size": 123,
        "digest": "sha256:test",
        "modified_at": "2026-03-18T00:00:00Z",
        "details": {"parameter_size": "7B"},
    },
    {
        "name": "llama3.2:latest",
        "model": "llama3.2:latest",
        "size": 456,
        "digest": "sha256:test-2",
        "modified_at": "2026-03-18T00:00:00Z",
        "details": {"parameter_size": "3.2B"},
    },
]


def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class FakeOllamaHandler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args) -> None:
        return

    def do_GET(self) -> None:
        if self.path == "/api/tags":
            self._send_json({"models": AVAILABLE_MODELS})
            return
        if self.path == "/api/version":
            self._send_json({"version": "0.18.0"})
            return
        self._send_json({"error": "not found"}, status=404)

    def do_POST(self) -> None:
        content_length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(content_length or 0)
        payload = json.loads(raw_body.decode("utf-8") or "{}")

        if self.path != "/api/generate":
            self._send_json({"error": "not found"}, status=404)
            return

        model = payload.get("model")
        if model not in {item["name"] for item in AVAILABLE_MODELS}:
            self._send_json({"error": "model not found"}, status=404)
            return

        if payload.get("stream"):
            self.send_response(200)
            self.send_header("Content-Type", "application/x-ndjson")
            self.end_headers()
            chunks = [
                {"model": model, "response": "Hello", "done": False},
                {"model": model, "response": "!", "done": False},
                {"model": model, "response": "", "done": True, "done_reason": "stop"},
            ]
            for chunk in chunks:
                self.wfile.write(json.dumps(chunk).encode("utf-8") + b"\n")
                self.wfile.flush()
            return

        prompt = payload.get("prompt", "")
        if "Summarize the following text." in prompt:
            response_text = "summary output"
        elif "Analyze the following" in prompt:
            response_text = "analysis output"
        else:
            response_text = "offline reply"

        self._send_json(
            {
                "model": model,
                "response": response_text,
                "done": True,
                "done_reason": "stop",
                "created_at": "2026-03-18T00:00:00Z",
            },
        )

    def _send_json(self, payload: dict, *, status: int = 200) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


class ApiRoutesTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.ollama_port = find_free_port()
        cls.api_port = find_free_port()
        cls.ollama_server = ThreadingHTTPServer(("127.0.0.1", cls.ollama_port), FakeOllamaHandler)
        cls.ollama_thread = threading.Thread(
            target=cls.ollama_server.serve_forever,
            daemon=True,
        )
        cls.ollama_thread.start()

        env = os.environ.copy()
        env.update(
            {
                "APP_ENV": "test",
                "API_HOST": "127.0.0.1",
                "API_PORT": str(cls.api_port),
                "LOG_LEVEL": "WARNING",
                "OLLAMA_BASE_URL": f"http://127.0.0.1:{cls.ollama_port}",
                "OLLAMA_TIMEOUT": "10",
                "DEFAULT_MODEL": "qwen2.5-coder:7b",
                "RATE_LIMIT_REQUESTS": "100",
                "RATE_LIMIT_WINDOW_SECONDS": "60",
                "MAX_CONCURRENT_AI_REQUESTS": "2",
                "QUEUE_WAIT_TIMEOUT": "2",
            },
        )
        cls.server_process = subprocess.Popen(
            [
                str(PYTHON_BIN),
                "-m",
                "uvicorn",
                "app.main:app",
                "--host",
                "127.0.0.1",
                "--port",
                str(cls.api_port),
            ],
            cwd=REPO_ROOT,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        cls._wait_for_server()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server_process.terminate()
        try:
            cls.server_process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            cls.server_process.kill()

        cls.ollama_server.shutdown()
        cls.ollama_server.server_close()
        cls.ollama_thread.join(timeout=5)

    @classmethod
    def _wait_for_server(cls) -> None:
        deadline = time.time() + 15
        while time.time() < deadline:
            try:
                status, _ = cls.request("GET", "/health")
                if status == 200:
                    return
            except Exception:
                time.sleep(0.2)
        raise RuntimeError("Timed out waiting for API server to start.")

    @classmethod
    def request(
        cls,
        method: str,
        path: str,
        payload: dict | None = None,
    ) -> tuple[int, dict | str]:
        body = None
        headers = {}
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
        request = urllib.request.Request(
            f"http://127.0.0.1:{cls.api_port}{path}",
            data=body,
            headers=headers,
            method=method,
        )
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                raw = response.read().decode("utf-8")
                return response.status, json.loads(raw)
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8")
            exc.close()
            return exc.code, json.loads(raw)

    def test_health_reports_reachable_ollama(self) -> None:
        status, payload = self.request("GET", "/health")
        self.assertEqual(status, 200)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["ollama_status"], "reachable")
        self.assertEqual(payload["available_models"], 2)

    def test_models_returns_local_models(self) -> None:
        status, payload = self.request("GET", "/models")
        self.assertEqual(status, 200)
        self.assertEqual(payload["count"], 2)
        self.assertEqual(payload["models"][0]["name"], "qwen2.5-coder:7b")

    def test_info_returns_server_capabilities(self) -> None:
        status, payload = self.request("GET", "/info")
        self.assertEqual(status, 200)
        self.assertEqual(payload["service"], "CoreAI Local")
        self.assertIn("chat-stream", payload["features"])
        self.assertIn("summarize", payload["features"])

    def test_chat_uses_default_model_when_request_does_not_override_it(self) -> None:
        status, payload = self.request("POST", "/chat", {"prompt": "Hello from LAN"})
        self.assertEqual(status, 200)
        self.assertEqual(payload["model"], "qwen2.5-coder:7b")
        self.assertEqual(payload["response"], "offline reply")

    def test_chat_rejects_unknown_model_with_structured_error(self) -> None:
        status, payload = self.request(
            "POST",
            "/chat",
            {"prompt": "Hello from LAN", "model": "missing:model"},
        )
        self.assertEqual(status, 404)
        self.assertEqual(payload["error"], "Requested model is not installed.")
        self.assertEqual(payload["code"], "model_not_installed")

    def test_chat_rejects_empty_prompt_with_validation_error(self) -> None:
        status, payload = self.request("POST", "/chat", {"prompt": "   "})
        self.assertEqual(status, 422)
        self.assertEqual(payload["error"], "Invalid request payload.")
        self.assertEqual(payload["code"], "validation_error")

    def test_summarize_endpoint(self) -> None:
        status, payload = self.request(
            "POST",
            "/summarize",
            {
                "text": "CoreAI-Local is an offline FastAPI gateway for Ollama.",
                "style": "brief",
                "model": "llama3.2:latest",
            },
        )
        self.assertEqual(status, 200)
        self.assertEqual(payload["summary"], "summary output")
        self.assertEqual(payload["model"], "llama3.2:latest")

    def test_analyze_code_endpoint(self) -> None:
        status, payload = self.request(
            "POST",
            "/analyze-code",
            {
                "code": "fun main() { println(\"Hi\") }",
                "language": "kotlin",
                "task": "explain",
                "model": "llama3.2:latest",
            },
        )
        self.assertEqual(status, 200)
        self.assertEqual(payload["analysis"], "analysis output")
        self.assertEqual(payload["language"], "kotlin")

    def test_chat_stream_endpoint(self) -> None:
        request = urllib.request.Request(
            f"http://127.0.0.1:{self.api_port}/chat/stream",
            data=json.dumps(
                {
                    "prompt": "Say hello in one short sentence.",
                    "model": "llama3.2:latest",
                },
            ).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=15) as response:
            body = response.read().decode("utf-8")

        self.assertIn('data: {"model": "llama3.2:latest", "chunk": "Hello"', body)
        self.assertIn('"done": true', body)
