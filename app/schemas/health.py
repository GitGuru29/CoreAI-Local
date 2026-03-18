from typing import Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    service: str
    version: str
    server_mode: str
    ollama_status: Literal["reachable", "unavailable"]
    ollama_available: bool
    default_model: str
    ollama_base_url: str
    ollama_version: str | None = None
    default_model_available: bool = False
    available_models: int = 0
    available_model_names: list[str] = Field(default_factory=list)
    detail: str | None = None
