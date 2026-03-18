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
    except (OllamaConnectionError, OllamaUpstreamError) as exc:
        return HealthResponse(
            status="degraded",
            service=settings.app_name,
            ollama_available=False,
            default_model=settings.default_model,
            ollama_base_url=settings.ollama_base_url,
            detail=exc.detail,
        )

    return HealthResponse(
        status="ok",
        service=settings.app_name,
        ollama_available=True,
        default_model=settings.default_model,
        ollama_base_url=settings.ollama_base_url,
        available_models=len(models),
        detail=None,
    )
