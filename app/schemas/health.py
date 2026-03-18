from typing import Literal

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    service: str
    ollama_available: bool
    default_model: str
    ollama_base_url: str
    available_models: int | None = None
    detail: str | None = None
