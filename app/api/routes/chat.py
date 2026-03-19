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
from app.services.task_prompts import build_chat_system_prompt
from app.utils.guards import enforce_max_length

router = APIRouter(tags=["chat"])
logger = get_logger(__name__)


def build_chat_messages(payload: ChatRequest) -> list[dict[str, str]]:
    messages = [{"role": item.role, "content": item.content} for item in payload.messages]
    if payload.prompt:
        messages.append({"role": "user", "content": payload.prompt})

    system_prompt = build_chat_system_prompt(
        system_prompt=payload.system_prompt,
        response_mode=payload.response_mode,
    )
    if system_prompt:
        messages.insert(0, {"role": "system", "content": system_prompt})
    return messages


def conversation_char_count(messages: list[dict[str, str]]) -> int:
    return sum(len(message.get("content", "")) for message in messages)


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
    messages = build_chat_messages(payload)
    enforce_max_length("conversation", " ".join(message["content"] for message in messages), settings.max_prompt_chars)
    await request_guard.enforce_rate_limit(client_ip)
    async with request_guard.acquire_generation_slot():
        await ollama_service.ensure_model_available(model_name)
        result = await ollama_service.chat(
            messages=messages,
            model=model_name,
            temperature=payload.temperature,
            keep_alive=payload.keep_alive,
        )
    message = result.get("message")
    response_text = ""
    if isinstance(message, dict):
        response_text = str(message.get("content") or "").strip()
    if not response_text:
        response_text = str(result.get("response") or "").strip()
    logger.info(
        "chat request completed client_ip=%s model=%s message_count=%s conversation_chars=%s",
        client_ip,
        model_name,
        len(messages),
        conversation_char_count(messages),
    )
    return ChatResponse(
        model=result.get("model", model_name),
        response=response_text,
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
    messages = build_chat_messages(payload)

    enforce_max_length("conversation", " ".join(message["content"] for message in messages), settings.max_prompt_chars)
    await request_guard.enforce_rate_limit(client_ip)
    await ollama_service.ensure_model_available(model_name)

    logger.info(
        "chat stream opened client_ip=%s model=%s message_count=%s conversation_chars=%s",
        client_ip,
        model_name,
        len(messages),
        conversation_char_count(messages),
    )

    async def event_stream():
        async with request_guard.acquire_generation_slot():
            async for chunk in ollama_service.stream_chat(
                messages=messages,
                model=model_name,
                temperature=payload.temperature,
                keep_alive=payload.keep_alive,
            ):
                message = chunk.get("message")
                chunk_text = chunk.get("response", "")
                if isinstance(message, dict):
                    chunk_text = message.get("content", "")
                event = {
                    "model": chunk.get("model", model_name),
                    "chunk": chunk_text,
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
