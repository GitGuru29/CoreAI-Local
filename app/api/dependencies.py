from fastapi import Request

from app.core.config import Settings
from app.services.ollama import OllamaService


def get_settings_from_app(request: Request) -> Settings:
    return request.app.state.settings


def get_ollama_service(request: Request) -> OllamaService:
    settings = get_settings_from_app(request)
    return OllamaService(
        base_url=settings.ollama_base_url,
        timeout=settings.ollama_timeout,
        http_client=request.app.state.http_client,
    )
