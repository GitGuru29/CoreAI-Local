import unittest

from fastapi.testclient import TestClient

from app.api.dependencies import get_ollama_service
from app.main import app
from app.utils.errors import OllamaConnectionError


class SuccessfulOllamaService:
    def __init__(self) -> None:
        self.generate_calls: list[dict] = []

    async def list_models(self) -> list[dict]:
        return [
            {
                "name": "qwen2.5-coder:7b",
                "size": 123,
                "digest": "sha256:test",
                "modified_at": "2026-03-18T00:00:00Z",
                "details": {"parameter_size": "7B"},
            },
        ]

    async def generate(self, **kwargs) -> dict:
        self.generate_calls.append(kwargs)
        return {
            "model": kwargs["model"],
            "response": "offline reply",
            "done": True,
            "done_reason": "stop",
            "created_at": "2026-03-18T00:00:00Z",
        }


class UnavailableOllamaService:
    async def list_models(self) -> list[dict]:
        raise OllamaConnectionError(
            "Unable to connect to Ollama. Make sure Ollama is running locally.",
        )


class ApiRoutesTestCase(unittest.TestCase):
    def tearDown(self) -> None:
        app.dependency_overrides.clear()

    def test_health_reports_degraded_when_ollama_is_unavailable(self) -> None:
        app.dependency_overrides[get_ollama_service] = lambda: UnavailableOllamaService()

        with TestClient(app) as client:
            response = client.get("/health")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "degraded")
        self.assertFalse(payload["ollama_available"])

    def test_models_returns_local_models(self) -> None:
        app.dependency_overrides[get_ollama_service] = lambda: SuccessfulOllamaService()

        with TestClient(app) as client:
            response = client.get("/models")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["count"], 1)
        self.assertEqual(payload["models"][0]["name"], "qwen2.5-coder:7b")

    def test_chat_uses_default_model_when_request_does_not_override_it(self) -> None:
        service = SuccessfulOllamaService()
        app.dependency_overrides[get_ollama_service] = lambda: service

        with TestClient(app) as client:
            response = client.post("/chat", json={"prompt": "Hello from LAN"})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["model"], "qwen2.5-coder:7b")
        self.assertEqual(payload["response"], "offline reply")
        self.assertEqual(service.generate_calls[0]["model"], "qwen2.5-coder:7b")
