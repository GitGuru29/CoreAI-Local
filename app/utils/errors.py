from typing import Any


class AppError(Exception):
    def __init__(
        self,
        error: str,
        *,
        status_code: int = 500,
        code: str = "app_error",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(error)
        self.error = error
        self.status_code = status_code
        self.code = code
        self.details = details or {}

    @property
    def detail(self) -> str:
        return self.error


class BadRequestError(AppError):
    def __init__(
        self,
        error: str = "Invalid request.",
        *,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            error,
            status_code=400,
            code="bad_request",
            details=details,
        )


class InputTooLargeError(AppError):
    def __init__(self, field_name: str, max_length: int, actual_length: int) -> None:
        super().__init__(
            f"{field_name} exceeds the configured size limit.",
            status_code=413,
            code="payload_too_large",
            details={
                "field": field_name,
                "max_length": max_length,
                "actual_length": actual_length,
            },
        )


class ModelNotInstalledError(AppError):
    def __init__(self, model_name: str, available_models: list[str] | None = None) -> None:
        details: dict[str, Any] = {"model": model_name}
        if available_models is not None:
            details["available_models"] = available_models
        super().__init__(
            "Requested model is not installed.",
            status_code=404,
            code="model_not_installed",
            details=details,
        )


class OllamaConnectionError(AppError):
    def __init__(
        self,
        detail: str = "Unable to connect to Ollama at the configured local endpoint.",
    ) -> None:
        super().__init__(
            detail,
            status_code=503,
            code="ollama_unavailable",
        )


class OllamaTimeoutError(AppError):
    def __init__(self, timeout_seconds: float) -> None:
        super().__init__(
            "Ollama timed out while generating a response.",
            status_code=504,
            code="ollama_timeout",
            details={"timeout_seconds": timeout_seconds},
        )


class OllamaUpstreamError(AppError):
    def __init__(
        self,
        detail: str,
        status_code: int = 502,
        *,
        code: str = "ollama_upstream_error",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            detail,
            status_code=status_code,
            code=code,
            details=details,
        )
