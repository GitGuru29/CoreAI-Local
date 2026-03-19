from functools import lru_cache

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = Field(default="CoreAI Local")
    app_version: str = Field(default="0.1.0")
    app_env: str = Field(default="development")
    server_mode: str = Field(default="offline-local")
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000, ge=1, le=65535)
    auth_enabled: bool = Field(default=False)
    auth_api_key: str = Field(default="")
    auth_exempt_paths: str = Field(default="/health,/info,/docs,/openapi.json,/redoc")
    log_level: str = Field(default="INFO")
    log_dir: str = Field(default="logs")
    log_file: str = Field(default="server.log")
    ollama_base_url: str = Field(default="http://localhost:11434")
    ollama_timeout: float = Field(default=1800.0, gt=0)
    default_model: str = Field(default="qwen2.5-coder:7b")
    max_prompt_chars: int = Field(default=12000, ge=1)
    max_text_chars: int = Field(default=24000, ge=1)
    max_code_chars: int = Field(default=32000, ge=1)
    max_task_chars: int = Field(default=1000, ge=1)
    rate_limit_requests: int = Field(default=30, ge=1)
    rate_limit_window_seconds: int = Field(default=60, ge=1)
    max_concurrent_ai_requests: int = Field(default=2, ge=1)
    queue_wait_timeout: float = Field(default=5.0, gt=0)
    cors_allowed_origins: str = Field(default="")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("log_level")
    @classmethod
    def normalize_log_level(cls, value: str) -> str:
        normalized = value.upper()
        valid_levels = {"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"}
        if normalized not in valid_levels:
            raise ValueError(
                f"LOG_LEVEL must be one of: {', '.join(sorted(valid_levels))}",
            )
        return normalized

    @field_validator("ollama_base_url")
    @classmethod
    def normalize_ollama_base_url(cls, value: str) -> str:
        return value.rstrip("/")

    @field_validator("auth_api_key")
    @classmethod
    def normalize_auth_api_key(cls, value: str) -> str:
        return value.strip()

    @model_validator(mode="after")
    def validate_auth_settings(self):
        if self.auth_enabled and not self.auth_api_key:
            raise ValueError("AUTH_API_KEY must be set when AUTH_ENABLED=true")
        return self

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]

    @property
    def auth_exempt_path_list(self) -> list[str]:
        return [path.strip() for path in self.auth_exempt_paths.split(",") if path.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
