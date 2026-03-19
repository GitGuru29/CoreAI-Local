from time import perf_counter

from starlette.datastructures import Headers

from app.core.logging import get_logger
from app.services.auth import AuthService

logger = get_logger(__name__)


class AccessLogMiddleware:
    def __init__(self, app) -> None:
        self.app = app

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start = perf_counter()
        client = scope.get("client")
        client_ip = client[0] if client else "unknown"
        method = scope.get("method", "-")
        path = scope.get("path", "-")
        status_code = 500

        async def send_wrapper(message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception:
            elapsed_ms = (perf_counter() - start) * 1000
            logger.exception(
                "client_ip=%s method=%s path=%s model=%s failed_in_ms=%.2f",
                client_ip,
                method,
                path,
                self._extract_selected_model(scope),
                elapsed_ms,
            )
            raise

        elapsed_ms = (perf_counter() - start) * 1000
        logger.info(
            "client_ip=%s method=%s path=%s status=%s model=%s duration_ms=%.2f",
            client_ip,
            method,
            path,
            status_code,
            self._extract_selected_model(scope),
            elapsed_ms,
        )

    @staticmethod
    def _extract_selected_model(scope) -> str:
        state = scope.get("state")
        if state is None:
            return "-"
        if isinstance(state, dict):
            return state.get("selected_model", "-")
        return getattr(state, "selected_model", "-")


class ApiKeyAuthMiddleware:
    def __init__(self, app, *, auth_service: AuthService) -> None:
        self.app = app
        self.auth_service = auth_service

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        headers = Headers(scope=scope)
        self.auth_service.authenticate(path=path, headers=headers)
        await self.app(scope, receive, send)
