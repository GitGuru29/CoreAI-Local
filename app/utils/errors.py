class AppError(Exception):
    def __init__(self, detail: str, status_code: int = 500) -> None:
        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code


class OllamaConnectionError(AppError):
    def __init__(
        self,
        detail: str = "Unable to connect to Ollama at the configured local endpoint.",
    ) -> None:
        super().__init__(detail=detail, status_code=503)


class OllamaUpstreamError(AppError):
    def __init__(self, detail: str, status_code: int = 502) -> None:
        super().__init__(detail=detail, status_code=status_code)
