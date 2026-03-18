from fastapi import APIRouter, Depends

from app.api.dependencies import get_ollama_service, get_settings_from_app
from app.core.config import Settings
from app.schemas.health import HealthResponse
from app.services.ollama import OllamaService
from app.utils.errors import OllamaConnectionError, OllamaUpstreamError

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse, summary="Check gateway health")
async def read_health(
    settings: Settings = Depends(get_settings_from_app),
    ollama_service: OllamaService = Depends(get_ollama_service),
) -> HealthResponse:
    try:
        models = await ollama_service.list_models()
        model_names = ollama_service.model_names_from_models(models)
        ollama_version = await ollama_service.get_version()
    except (OllamaConnectionError, OllamaUpstreamError) as exc:
        return HealthResponse(
            status="degraded",
            service=settings.app_name,
            version=settings.app_version,
            server_mode=settings.server_mode,
            ollama_status="unavailable",
            ollama_available=False,
            default_model=settings.default_model,
            ollama_base_url=settings.ollama_base_url,
            default_model_available=False,
            available_models=0,
            available_model_names=[],
            detail=exc.error,
        )

    return HealthResponse(
        status="ok",
        service=settings.app_name,
        version=settings.app_version,
        server_mode=settings.server_mode,
        ollama_status="reachable",
        ollama_available=True,
        default_model=settings.default_model,
        ollama_base_url=settings.ollama_base_url,
        ollama_version=ollama_version,
        default_model_available=settings.default_model in model_names,
        available_models=len(model_names),
        available_model_names=model_names,
        detail=None,
    )
