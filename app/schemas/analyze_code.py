from typing import Literal

from pydantic import BaseModel, Field, field_validator


class AnalyzeCodeRequest(BaseModel):
    code: str = Field(..., min_length=1, description="Source code to analyze.")
    language: str = Field(default="text", description="Language hint such as python or kotlin.")
    task: Literal["explain", "review", "find-bugs", "clean-up", "document", "optimize"] = (
        "explain"
    )
    instructions: str | None = Field(default=None, description="Optional extra instruction.")
    model: str | None = Field(default=None, description="Optional model override.")
    system_prompt: str | None = Field(default=None, description="Optional system instruction.")
    temperature: float | None = Field(default=None, ge=0, le=2)
    keep_alive: str | None = Field(default=None, description="Optional Ollama keep_alive value.")

    @field_validator("code")
    @classmethod
    def validate_code(cls, value: str) -> str:
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("Code must not be empty.")
        return trimmed

    @field_validator("language")
    @classmethod
    def normalize_language(cls, value: str) -> str:
        trimmed = value.strip()
        return trimmed or "text"

    @field_validator("instructions", "model", "system_prompt", "keep_alive")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        trimmed = value.strip()
        return trimmed or None


class AnalyzeCodeResponse(BaseModel):
    model: str
    language: str
    task: str
    analysis: str
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
