from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.logging import get_logger
from app.utils.errors import AppError

logger = get_logger(__name__)


async def app_error_handler(request: Request, exc: Exception) -> JSONResponse:
    if isinstance(exc, AppError):
        status_code = exc.status_code
        detail = exc.detail
    else:
        status_code = 500
        detail = "Internal server error."
        logger.exception(
            "Unhandled error on %s %s",
            request.method,
            request.url.path,
        )

    return JSONResponse(status_code=status_code, content={"detail": detail})


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    logger.warning(
        "Validation failed on %s %s",
        request.method,
        request.url.path,
    )
    return JSONResponse(status_code=422, content={"detail": exc.errors()})
