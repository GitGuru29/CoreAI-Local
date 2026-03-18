import unittest

import httpx

from app.api.dependencies import get_ollama_service
from app.core.config import get_settings
from app.main import app
from app.services.request_guard import RequestGuardService
from app.utils.errors import ModelNotInstalledError, OllamaConnectionError


class SuccessfulOllamaService:
    def __init__(self) -> None:
        self.generate_calls: list[dict] = []
        self.models = [
            {
                "name": "qwen2.5-coder:7b",
                "size": 123,
                "digest": "sha256:test",
                "modified_at": "2026-03-18T00:00:00Z",
                "details": {"parameter_size": "7B"},
            },
            {
                "name": "llama3.2:latest",
                "size": 456,
                "digest": "sha256:test-2",
                "modified_at": "2026-03-18T00:00:00Z",
                "details": {"parameter_size": "3.2B"},
            },
        ]

    async def list_models(self) -> list[dict]:
        return self.models

    async def list_model_names(self) -> list[str]:
        return [model["name"] for model in self.models]

    async def ensure_model_available(self, model: str) -> list[str]:
        model_names = await self.list_model_names()
        if model not in model_names:
            raise ModelNotInstalledError(model, available_models=model_names)
        return model_names

    async def get_version(self) -> str | None:
        return "0.7.0"

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

    async def get_version(self) -> str | None:
        raise OllamaConnectionError(
            "Unable to connect to Ollama. Make sure Ollama is running locally.",
        )


class ApiRoutesTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        app.state.settings = get_settings()
        app.state.http_client = None
        app.state.request_guard = RequestGuardService(
            max_requests=30,
            window_seconds=60,
            max_concurrent_requests=2,
            acquire_timeout=5,
        )
        transport = httpx.ASGITransport(app=app)
        self.client = httpx.AsyncClient(transport=transport, base_url="http://testserver")

    async def asyncTearDown(self) -> None:
        await self.client.aclose()
        app.dependency_overrides.clear()

    async def test_health_reports_degraded_when_ollama_is_unavailable(self) -> None:
        app.dependency_overrides[get_ollama_service] = lambda: UnavailableOllamaService()

        response = await self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "degraded")
        self.assertFalse(payload["ollama_available"])
        self.assertEqual(payload["ollama_status"], "unavailable")

    async def test_models_returns_local_models(self) -> None:
        app.dependency_overrides[get_ollama_service] = lambda: SuccessfulOllamaService()

        response = await self.client.get("/models")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["count"], 2)
        self.assertEqual(payload["models"][0]["name"], "qwen2.5-coder:7b")

    async def test_chat_uses_default_model_when_request_does_not_override_it(self) -> None:
        service = SuccessfulOllamaService()
        app.dependency_overrides[get_ollama_service] = lambda: service

        response = await self.client.post("/chat", json={"prompt": "Hello from LAN"})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["model"], "qwen2.5-coder:7b")
        self.assertEqual(payload["response"], "offline reply")
        self.assertEqual(service.generate_calls[0]["model"], "qwen2.5-coder:7b")

    async def test_chat_rejects_unknown_model_with_structured_error(self) -> None:
        app.dependency_overrides[get_ollama_service] = lambda: SuccessfulOllamaService()

        response = await self.client.post(
            "/chat",
            json={"prompt": "Hello from LAN", "model": "missing:model"},
        )

        self.assertEqual(response.status_code, 404)
        payload = response.json()
        self.assertEqual(payload["error"], "Requested model is not installed.")
        self.assertEqual(payload["code"], "model_not_installed")

    async def test_chat_rejects_empty_prompt_with_validation_error(self) -> None:
        app.dependency_overrides[get_ollama_service] = lambda: SuccessfulOllamaService()

        response = await self.client.post("/chat", json={"prompt": "   "})

        self.assertEqual(response.status_code, 422)
        payload = response.json()
        self.assertEqual(payload["error"], "Invalid request payload.")
        self.assertEqual(payload["code"], "validation_error")

    async def test_info_returns_server_capabilities(self) -> None:
        app.dependency_overrides[get_ollama_service] = lambda: SuccessfulOllamaService()

        response = await self.client.get("/info")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["service"], "CoreAI Local")
        self.assertIn("chat", payload["features"])
