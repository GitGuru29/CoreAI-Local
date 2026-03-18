from pydantic import BaseModel, Field


class ServerInfoResponse(BaseModel):
    service: str
    version: str
    environment: str
    server_mode: str
    offline_mode: bool
    api_host: str
    api_port: int
    ollama_base_url: str
    ollama_timeout: float
    ollama_status: str
    default_model: str
    max_prompt_chars: int
    available_model_names: list[str] = Field(default_factory=list)
    features: list[str] = Field(default_factory=list)
    detail: str | None = None
