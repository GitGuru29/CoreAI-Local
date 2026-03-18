from typing import Literal

from pydantic import BaseModel, Field, field_validator


class SummarizeRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Text to summarize.")
    model: str | None = Field(default=None, description="Optional model override.")
    style: Literal["brief", "balanced", "detailed"] = "balanced"
    max_bullets: int | None = Field(default=None, ge=1, le=20)
    system_prompt: str | None = Field(default=None, description="Optional system instruction.")
    temperature: float | None = Field(default=None, ge=0, le=2)
    keep_alive: str | None = Field(default=None, description="Optional Ollama keep_alive value.")

    @field_validator("text")
    @classmethod
    def validate_text(cls, value: str) -> str:
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("Text must not be empty.")
        return trimmed

    @field_validator("model", "system_prompt", "keep_alive")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        trimmed = value.strip()
        return trimmed or None


class SummarizeResponse(BaseModel):
    model: str
    summary: str
    style: str
    source_length: int
    done: bool
    done_reason: str | None = None
    created_at: str | None = None
    total_duration: int | None = None
    load_duration: int | None = None
    prompt_eval_count: int | None = None
    eval_count: int | None = None
    prompt_eval_duration: int | None = None
    eval_duration: int | None = None
