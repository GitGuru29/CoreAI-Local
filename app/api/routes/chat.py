import json

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from app.api.dependencies import (
    get_ollama_service,
    get_request_guard,
    get_settings_from_app,
)
from app.core.config import Settings
from app.core.logging import get_logger
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.ollama import OllamaService
from app.services.request_guard import RequestGuardService
from app.utils.guards import enforce_max_length

router = APIRouter(tags=["chat"])
logger = get_logger(__name__)


@router.post("/chat", response_model=ChatResponse, summary="Generate a response")
async def create_chat_completion(
    payload: ChatRequest,
    request: Request,
    settings: Settings = Depends(get_settings_from_app),
    ollama_service: OllamaService = Depends(get_ollama_service),
    request_guard: RequestGuardService = Depends(get_request_guard),
) -> ChatResponse:
    model_name = payload.model or settings.default_model
    client_ip = request.client.host if request.client else "unknown"
    request.state.selected_model = model_name
    enforce_max_length("prompt", payload.prompt, settings.max_prompt_chars)
    await request_guard.enforce_rate_limit(client_ip)
    async with request_guard.acquire_generation_slot():
        await ollama_service.ensure_model_available(model_name)
        result = await ollama_service.generate(
            prompt=payload.prompt,
            model=model_name,
            system_prompt=payload.system_prompt,
            temperature=payload.temperature,
            keep_alive=payload.keep_alive,
        )
    logger.info(
        "chat request completed client_ip=%s model=%s prompt_chars=%s",
        client_ip,
        model_name,
        len(payload.prompt),
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


@router.post("/chat/stream", summary="Stream a response as server-sent events")
async def stream_chat_completion(
    payload: ChatRequest,
    request: Request,
    settings: Settings = Depends(get_settings_from_app),
    ollama_service: OllamaService = Depends(get_ollama_service),
    request_guard: RequestGuardService = Depends(get_request_guard),
) -> StreamingResponse:
    model_name = payload.model or settings.default_model
    client_ip = request.client.host if request.client else "unknown"
    request.state.selected_model = model_name

    enforce_max_length("prompt", payload.prompt, settings.max_prompt_chars)
    await request_guard.enforce_rate_limit(client_ip)
    await ollama_service.ensure_model_available(model_name)

    logger.info(
        "chat stream opened client_ip=%s model=%s prompt_chars=%s",
        client_ip,
        model_name,
        len(payload.prompt),
    )

    async def event_stream():
        async with request_guard.acquire_generation_slot():
            async for chunk in ollama_service.stream_generate(
                prompt=payload.prompt,
                model=model_name,
                system_prompt=payload.system_prompt,
                temperature=payload.temperature,
                keep_alive=payload.keep_alive,
            ):
                event = {
                    "model": chunk.get("model", model_name),
                    "chunk": chunk.get("response", ""),
                    "done": chunk.get("done", False),
                    "done_reason": chunk.get("done_reason"),
                    "created_at": chunk.get("created_at"),
                    "total_duration": chunk.get("total_duration"),
                    "load_duration": chunk.get("load_duration"),
                    "prompt_eval_count": chunk.get("prompt_eval_count"),
                    "eval_count": chunk.get("eval_count"),
                }
                yield f"data: {json.dumps(event, ensure_ascii=True)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache"},
    )
