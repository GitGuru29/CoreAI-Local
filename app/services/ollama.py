from typing import Any

import httpx

from app.core.logging import get_logger
from app.utils.errors import OllamaConnectionError, OllamaUpstreamError

logger = get_logger(__name__)


class OllamaService:
    def __init__(
        self,
        *,
        base_url: str,
        timeout: float,
        http_client: httpx.AsyncClient,
    ) -> None:
        self.base_url = base_url
        self.timeout = timeout
        self.http_client = http_client

    async def list_models(self) -> list[dict[str, Any]]:
        payload = await self._request("GET", "/api/tags")
        models = payload.get("models", [])
        if not isinstance(models, list):
            raise OllamaUpstreamError("Ollama returned an invalid models payload.")
        return models

    async def generate(
        self,
        *,
        prompt: str,
        model: str,
        system_prompt: str | None = None,
        temperature: float | None = None,
        keep_alive: str | None = None,
    ) -> dict[str, Any]:
        request_payload: dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "stream": False,
        }
        if system_prompt:
            request_payload["system"] = system_prompt
        if keep_alive:
            request_payload["keep_alive"] = keep_alive
        if temperature is not None:
            request_payload["options"] = {"temperature": temperature}

        return await self._request("POST", "/api/generate", request_payload)

    async def _request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        try:
            response = await self.http_client.request(
                method=method,
                url=url,
                json=payload,
                timeout=self.timeout,
            )
        except httpx.RequestError as exc:
            logger.error("Unable to reach Ollama at %s: %s", url, exc)
            raise OllamaConnectionError(
                "Unable to connect to Ollama. Make sure Ollama is running locally.",
            ) from exc

        if response.status_code >= 400:
            detail = self._extract_error_detail(response)
            mapped_status = 502
            if response.status_code in {400, 404, 422, 503}:
                mapped_status = response.status_code
            logger.error(
                "Ollama request failed: %s %s -> %s (%s)",
                method,
                path,
                response.status_code,
                detail,
            )
            raise OllamaUpstreamError(detail, status_code=mapped_status)

        try:
            data = response.json()
        except ValueError as exc:
            raise OllamaUpstreamError(
                "Ollama returned an invalid JSON response.",
            ) from exc

        if not isinstance(data, dict):
            raise OllamaUpstreamError("Ollama returned an invalid response payload.")
        return data

    @staticmethod
    def _extract_error_detail(response: httpx.Response) -> str:
        try:
            payload = response.json()
        except ValueError:
            return response.text.strip() or "Ollama returned an unknown error."

        if isinstance(payload, dict):
            for key in ("error", "message", "detail"):
                value = payload.get(key)
                if isinstance(value, str) and value.strip():
                    return value
        return "Ollama returned an unknown error."
