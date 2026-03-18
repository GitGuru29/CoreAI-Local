from fastapi import APIRouter, Depends

from app.api.dependencies import get_ollama_service, get_settings_from_app
from app.core.config import Settings
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.ollama import OllamaService

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse, summary="Generate a response")
async def create_chat_completion(
    payload: ChatRequest,
    settings: Settings = Depends(get_settings_from_app),
    ollama_service: OllamaService = Depends(get_ollama_service),
) -> ChatResponse:
    model_name = payload.model or settings.default_model
    result = await ollama_service.generate(
        prompt=payload.prompt,
        model=model_name,
        system_prompt=payload.system_prompt,
        temperature=payload.temperature,
        keep_alive=payload.keep_alive,
    )
    return ChatResponse(
        model=result.get("model", model_name),
        response=(result.get("response") or "").strip(),
        done=result.get("done", True),
        done_reason=result.get("done_reason"),
        created_at=result.get("created_at"),
        total_duration=result.get("total_duration"),
        load_duration=result.get("load_duration"),
        prompt_eval_count=result.get("prompt_eval_count"),
        eval_count=result.get("eval_count"),
        prompt_eval_duration=result.get("prompt_eval_duration"),
        eval_duration=result.get("eval_duration"),
    )
