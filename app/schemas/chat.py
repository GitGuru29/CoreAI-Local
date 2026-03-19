from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str = Field(..., min_length=1, description="Message text for the chat history.")

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("Message content must not be empty.")
        return trimmed


class ChatRequest(BaseModel):
    prompt: str | None = Field(
        default=None,
        description="Optional latest user prompt. Can be used together with messages.",
    )
    messages: list[ChatMessage] = Field(
        default_factory=list,
        description="Optional prior conversation history.",
    )
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
    response_mode: Literal["auto", "guide", "code"] = Field(
        default="auto",
        description="Optional response preference to bias toward guidance or concrete code.",
    )

    @field_validator("prompt")
    @classmethod
    def validate_prompt(cls, value: str | None) -> str | None:
        if value is None:
            return None
        trimmed = value.strip()
        if not trimmed:
            return None
        return trimmed

    @field_validator("model", "system_prompt", "keep_alive")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        trimmed = value.strip()
        return trimmed or None

    @model_validator(mode="after")
    def validate_prompt_or_messages(self):
        if not self.prompt and not self.messages:
            raise ValueError("Either prompt or messages must be provided.")
        return self


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
