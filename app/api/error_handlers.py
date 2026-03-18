from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.logging import get_logger
from app.utils.errors import AppError

logger = get_logger(__name__)


async def app_error_handler(request: Request, exc: Exception) -> JSONResponse:
    if isinstance(exc, AppError):
        status_code = exc.status_code
        content = {"error": exc.error, "code": exc.code}
        if exc.details:
            content["details"] = exc.details
    else:
        status_code = 500
        content = {"error": "Internal server error.", "code": "internal_server_error"}
        logger.exception(
            "Unhandled error on %s %s",
            request.method,
            request.url.path,
        )

    return JSONResponse(status_code=status_code, content=content)


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    logger.warning(
        "Validation failed on %s %s",
        request.method,
        request.url.path,
    )
    return JSONResponse(
        status_code=422,
        content={
            "error": "Invalid request payload.",
            "code": "validation_error",
            "details": exc.errors(),
        },
    )
