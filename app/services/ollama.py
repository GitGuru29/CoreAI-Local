import json
from collections.abc import AsyncIterator
from typing import Any

import httpx

from app.core.logging import get_logger
from app.utils.errors import (
    ModelNotInstalledError,
    OllamaConnectionError,
    OllamaTimeoutError,
    OllamaUpstreamError,
)

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

    async def list_model_names(self) -> list[str]:
        return self.model_names_from_models(await self.list_models())

    async def ensure_model_available(self, model: str) -> list[str]:
        model_names = await self.list_model_names()
        if model not in model_names:
            raise ModelNotInstalledError(model, available_models=model_names)
        return model_names

    async def get_version(self) -> str | None:
        payload = await self._request("GET", "/api/version")
        version = payload.get("version")
        return version if isinstance(version, str) else None

    async def generate(
        self,
        *,
        prompt: str,
        model: str,
        system_prompt: str | None = None,
        temperature: float | None = None,
        keep_alive: str | None = None,
    ) -> dict[str, Any]:
        request_payload = self._build_generate_payload(
            prompt=prompt,
            model=model,
            system_prompt=system_prompt,
            temperature=temperature,
            keep_alive=keep_alive,
            stream=False,
        )
        return await self._request("POST", "/api/generate", request_payload)

    async def chat(
        self,
        *,
        messages: list[dict[str, str]],
        model: str,
        temperature: float | None = None,
        keep_alive: str | None = None,
    ) -> dict[str, Any]:
        request_payload = self._build_chat_payload(
            messages=messages,
            model=model,
            temperature=temperature,
            keep_alive=keep_alive,
            stream=False,
        )
        return await self._request("POST", "/api/chat", request_payload)

    def stream_generate(
        self,
        *,
        prompt: str,
        model: str,
        system_prompt: str | None = None,
        temperature: float | None = None,
        keep_alive: str | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        request_payload = self._build_generate_payload(
            prompt=prompt,
            model=model,
            system_prompt=system_prompt,
            temperature=temperature,
            keep_alive=keep_alive,
            stream=True,
        )

        async def iterator() -> AsyncIterator[dict[str, Any]]:
            url = f"{self.base_url}/api/generate"
            try:
                async with self.http_client.stream(
                    "POST",
                    url,
                    json=request_payload,
                    timeout=self.timeout,
                ) as response:
                    if response.status_code >= 400:
                        detail = self._extract_error_detail(response)
                        mapped_status = 502
                        if response.status_code in {400, 404, 422, 503}:
                            mapped_status = response.status_code
                        raise OllamaUpstreamError(detail, status_code=mapped_status)

                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        try:
                            payload = json.loads(line)
                        except json.JSONDecodeError as exc:
                            raise OllamaUpstreamError(
                                "Ollama returned an invalid JSON stream payload.",
                            ) from exc
                        if not isinstance(payload, dict):
                            raise OllamaUpstreamError(
                                "Ollama returned an invalid stream payload.",
                            )
                        yield payload
            except httpx.TimeoutException as exc:
                logger.error("Ollama timed out after %s seconds for %s", self.timeout, url)
                raise OllamaTimeoutError(self.timeout) from exc
            except httpx.RequestError as exc:
                logger.error("Unable to reach Ollama at %s: %s", url, exc)
                raise OllamaConnectionError(
                    "Unable to connect to Ollama. Make sure Ollama is running locally.",
                ) from exc

        return iterator()

    def stream_chat(
        self,
        *,
        messages: list[dict[str, str]],
        model: str,
        temperature: float | None = None,
        keep_alive: str | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        request_payload = self._build_chat_payload(
            messages=messages,
            model=model,
            temperature=temperature,
            keep_alive=keep_alive,
            stream=True,
        )

        async def iterator() -> AsyncIterator[dict[str, Any]]:
            url = f"{self.base_url}/api/chat"
            try:
                async with self.http_client.stream(
                    "POST",
                    url,
                    json=request_payload,
                    timeout=self.timeout,
                ) as response:
                    if response.status_code >= 400:
                        detail = self._extract_error_detail(response)
                        mapped_status = 502
                        if response.status_code in {400, 404, 422, 503}:
                            mapped_status = response.status_code
                        raise OllamaUpstreamError(detail, status_code=mapped_status)

                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        try:
                            payload = json.loads(line)
                        except json.JSONDecodeError as exc:
                            raise OllamaUpstreamError(
                                "Ollama returned an invalid JSON stream payload.",
                            ) from exc
                        if not isinstance(payload, dict):
                            raise OllamaUpstreamError(
                                "Ollama returned an invalid stream payload.",
                            )
                        yield payload
            except httpx.TimeoutException as exc:
                logger.error("Ollama timed out after %s seconds for %s", self.timeout, url)
                raise OllamaTimeoutError(self.timeout) from exc
            except httpx.RequestError as exc:
                logger.error("Unable to reach Ollama at %s: %s", url, exc)
                raise OllamaConnectionError(
                    "Unable to connect to Ollama. Make sure Ollama is running locally.",
                ) from exc

        return iterator()

    async def _request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        try:
            logger.debug("Sending Ollama request %s %s", method, path)
            response = await self.http_client.request(
                method=method,
                url=url,
                json=payload,
                timeout=self.timeout,
            )
        except httpx.TimeoutException as exc:
            logger.error("Ollama timed out after %s seconds for %s", self.timeout, url)
            raise OllamaTimeoutError(self.timeout) from exc
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
    def model_names_from_models(models: list[dict[str, Any]]) -> list[str]:
        names: list[str] = []
        for model in models:
            name = model.get("name") or model.get("model")
            if isinstance(name, str) and name:
                names.append(name)
        return names

    @staticmethod
    def _build_generate_payload(
        *,
        prompt: str,
        model: str,
        system_prompt: str | None,
        temperature: float | None,
        keep_alive: str | None,
        stream: bool,
    ) -> dict[str, Any]:
        request_payload: dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "stream": stream,
        }
        if system_prompt:
            request_payload["system"] = system_prompt
        if keep_alive:
            request_payload["keep_alive"] = keep_alive
        if temperature is not None:
            request_payload["options"] = {"temperature": temperature}
        return request_payload

    @staticmethod
    def _build_chat_payload(
        *,
        messages: list[dict[str, str]],
        model: str,
        temperature: float | None,
        keep_alive: str | None,
        stream: bool,
    ) -> dict[str, Any]:
        request_payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": stream,
        }
        if keep_alive:
            request_payload["keep_alive"] = keep_alive
        if temperature is not None:
            request_payload["options"] = {"temperature": temperature}
        return request_payload

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
