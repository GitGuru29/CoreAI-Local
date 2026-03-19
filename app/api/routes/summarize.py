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
from app.schemas.summarize import SummarizeRequest, SummarizeResponse
from app.services.ollama import OllamaService
from app.services.request_guard import RequestGuardService
from app.services.task_prompts import build_summary_prompt
from app.utils.guards import enforce_max_length

router = APIRouter(tags=["summarize"])
logger = get_logger(__name__)


@router.post(
    "/summarize",
    response_model=SummarizeResponse,
    summary="Summarize text with a local model",
)
async def summarize_text(
    payload: SummarizeRequest,
    request: Request,
    settings: Settings = Depends(get_settings_from_app),
    ollama_service: OllamaService = Depends(get_ollama_service),
    request_guard: RequestGuardService = Depends(get_request_guard),
) -> SummarizeResponse:
    model_name = payload.model or settings.default_model
    client_ip = request.client.host if request.client else "unknown"
    request.state.selected_model = model_name

    enforce_max_length("text", payload.text, settings.max_text_chars)
    await request_guard.enforce_rate_limit(client_ip)

    prompt = build_summary_prompt(
        text=payload.text,
        style=payload.style,
        max_bullets=payload.max_bullets,
    )

    async with request_guard.acquire_generation_slot():
        await ollama_service.ensure_model_available(model_name)
        result = await ollama_service.generate(
            prompt=prompt,
            model=model_name,
            system_prompt=payload.system_prompt
            or "You are a precise offline summarization assistant.",
            temperature=payload.temperature,
            keep_alive=payload.keep_alive,
        )

    logger.info(
        "summarize request completed client_ip=%s model=%s text_chars=%s",
        client_ip,
        model_name,
        len(payload.text),
    )
    return SummarizeResponse(
        model=result.get("model", model_name),
        summary=(result.get("response") or "").strip(),
        style=payload.style,
        source_length=len(payload.text),
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


@router.post(
    "/summarize/stream",
    summary="Stream a summary as server-sent events",
)
async def stream_summary(
    payload: SummarizeRequest,
    request: Request,
    settings: Settings = Depends(get_settings_from_app),
    ollama_service: OllamaService = Depends(get_ollama_service),
    request_guard: RequestGuardService = Depends(get_request_guard),
) -> StreamingResponse:
    model_name = payload.model or settings.default_model
    client_ip = request.client.host if request.client else "unknown"
    request.state.selected_model = model_name

    enforce_max_length("text", payload.text, settings.max_text_chars)
    await request_guard.enforce_rate_limit(client_ip)

    prompt = build_summary_prompt(
        text=payload.text,
        style=payload.style,
        max_bullets=payload.max_bullets,
    )

    await ollama_service.ensure_model_available(model_name)

    logger.info(
        "summarize stream opened client_ip=%s model=%s text_chars=%s",
        client_ip,
        model_name,
        len(payload.text),
    )

    async def event_stream():
        async with request_guard.acquire_generation_slot():
            async for chunk in ollama_service.stream_generate(
                prompt=prompt,
                model=model_name,
                system_prompt=payload.system_prompt
                or "You are a precise offline summarization assistant.",
                temperature=payload.temperature,
                keep_alive=payload.keep_alive,
            ):
                event = {
                    "model": chunk.get("model", model_name),
                    "style": payload.style,
                    "source_length": len(payload.text),
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
