from pydantic import BaseModel, Field, field_validator


class ChatRequest(BaseModel):
    prompt: str = Field(..., min_length=1, description="Prompt sent to the model.")
    model: str | None = Field(
        default=None,
        description="Optional model override. Falls back to DEFAULT_MODEL.",
    )
    system_prompt: str | None = Field(
        default=None,
        description="Optional system instruction.",
    )
    temperature: float | None = Field(
        default=None,
        ge=0,
        le=2,
        description="Optional sampling temperature forwarded to Ollama.",
    )
    keep_alive: str | None = Field(
        default=None,
        description="Optional Ollama keep_alive value such as 5m.",
    )

    @field_validator("prompt")
    @classmethod
    def validate_prompt(cls, value: str) -> str:
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("Prompt must not be empty.")
        return trimmed

    @field_validator("model", "system_prompt", "keep_alive")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        trimmed = value.strip()
        return trimmed or None


class ChatResponse(BaseModel):
    model: str
    response: str
    done: bool
    done_reason: str | None = None
    created_at: str | None = None
    total_duration: int | None = None
    load_duration: int | None = None
    prompt_eval_count: int | None = None
    eval_count: int | None = None
    prompt_eval_duration: int | None = None
    eval_duration: int | None = None
