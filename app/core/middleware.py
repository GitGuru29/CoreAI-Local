from time import perf_counter

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import get_logger

logger = get_logger(__name__)


class AccessLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        start = perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            elapsed_ms = (perf_counter() - start) * 1000
            logger.exception(
                "%s %s failed in %.2f ms",
                request.method,
                request.url.path,
                elapsed_ms,
            )
            raise

        elapsed_ms = (perf_counter() - start) * 1000
        logger.info(
            "%s %s -> %s in %.2f ms",
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
        )
        return response
