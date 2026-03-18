from fastapi import APIRouter, Depends

from app.api.dependencies import get_ollama_service
from app.schemas.models import ModelInfo, ModelsResponse
from app.services.ollama import OllamaService

router = APIRouter(tags=["models"])


@router.get("/models", response_model=ModelsResponse, summary="List Ollama models")
async def read_models(
    ollama_service: OllamaService = Depends(get_ollama_service),
) -> ModelsResponse:
    models = await ollama_service.list_models()
    items = [
        ModelInfo(
            name=model.get("name") or model.get("model") or "unknown",
            size=model.get("size"),
            digest=model.get("digest"),
            modified_at=model.get("modified_at"),
            details=model.get("details"),
        )
        for model in models
    ]
    return ModelsResponse(count=len(items), models=items)
