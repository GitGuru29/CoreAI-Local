from fastapi import APIRouter, Depends, Request

from app.api.dependencies import (
    get_ollama_service,
    get_request_guard,
    get_settings_from_app,
)
from app.core.config import Settings
from app.core.logging import get_logger
from app.schemas.analyze_code import AnalyzeCodeRequest, AnalyzeCodeResponse
from app.services.ollama import OllamaService
from app.services.request_guard import RequestGuardService
from app.services.task_prompts import build_code_analysis_prompt
from app.utils.guards import enforce_max_length

router = APIRouter(tags=["analyze-code"])
logger = get_logger(__name__)


@router.post(
    "/analyze-code",
    response_model=AnalyzeCodeResponse,
    summary="Analyze code with a local model",
)
async def analyze_code(
    payload: AnalyzeCodeRequest,
    request: Request,
    settings: Settings = Depends(get_settings_from_app),
    ollama_service: OllamaService = Depends(get_ollama_service),
    request_guard: RequestGuardService = Depends(get_request_guard),
) -> AnalyzeCodeResponse:
    model_name = payload.model or settings.default_model
    client_ip = request.client.host if request.client else "unknown"
    request.state.selected_model = model_name

    enforce_max_length("code", payload.code, settings.max_code_chars)
    if payload.instructions:
        enforce_max_length("instructions", payload.instructions, settings.max_task_chars)
    await request_guard.enforce_rate_limit(client_ip)

    prompt = build_code_analysis_prompt(
        code=payload.code,
        language=payload.language,
        task=payload.task,
        instructions=payload.instructions,
    )

    async with request_guard.acquire_generation_slot():
        await ollama_service.ensure_model_available(model_name)
        result = await ollama_service.generate(
            prompt=prompt,
            model=model_name,
            system_prompt=payload.system_prompt
            or "You are a senior software engineer analyzing code offline.",
            temperature=payload.temperature,
            keep_alive=payload.keep_alive,
        )

    logger.info(
        "analyze-code request completed client_ip=%s model=%s language=%s code_chars=%s task=%s",
        client_ip,
        model_name,
        payload.language,
        len(payload.code),
        payload.task,
    )
    return AnalyzeCodeResponse(
        model=result.get("model", model_name),
        language=payload.language,
        task=payload.task,
        analysis=(result.get("response") or "").strip(),
        source_length=len(payload.code),
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
