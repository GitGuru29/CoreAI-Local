from fastapi import APIRouter, Depends

from app.api.dependencies import get_ollama_service, get_settings_from_app
from app.core.config import Settings
from app.schemas.info import ServerInfoResponse
from app.services.ollama import OllamaService
from app.utils.errors import OllamaConnectionError, OllamaUpstreamError

router = APIRouter(tags=["info"])


@router.get("/info", response_model=ServerInfoResponse, summary="Get server info")
async def read_server_info(
    settings: Settings = Depends(get_settings_from_app),
    ollama_service: OllamaService = Depends(get_ollama_service),
) -> ServerInfoResponse:
    try:
        model_names = await ollama_service.list_model_names()
        ollama_status = "reachable"
        detail = None
    except (OllamaConnectionError, OllamaUpstreamError) as exc:
        model_names = []
        ollama_status = "unavailable"
        detail = exc.error

    return ServerInfoResponse(
        service=settings.app_name,
        version=settings.app_version,
        environment=settings.app_env,
        server_mode=settings.server_mode,
        offline_mode=True,
        api_host=settings.api_host,
        api_port=settings.api_port,
        ollama_base_url=settings.ollama_base_url,
        ollama_timeout=settings.ollama_timeout,
        ollama_status=ollama_status,
        default_model=settings.default_model,
        max_prompt_chars=settings.max_prompt_chars,
        available_model_names=model_names,
        features=[
            "chat",
            "models",
            "health",
            "info",
            "model-validation",
            "structured-errors",
            "file-logging",
            "request-guard",
        ],
        detail=detail,
    )
