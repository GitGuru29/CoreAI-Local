from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from app.api.error_handlers import app_error_handler, validation_exception_handler
from app.api.router import api_router
from app.core.config import get_settings
from app.core.logging import get_logger, setup_logging
from app.core.middleware import AccessLogMiddleware
from app.utils.errors import AppError

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(application: FastAPI):
    settings = get_settings()
    setup_logging(settings.log_level)
    application.state.settings = settings
    application.state.http_client = httpx.AsyncClient()
    logger.info(
        "Starting %s on %s:%s",
        settings.app_name,
        settings.api_host,
        settings.api_port,
    )
    try:
        yield
    finally:
        await application.state.http_client.aclose()
        logger.info("Shutting down %s", settings.app_name)


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )
    application.add_middleware(AccessLogMiddleware)
    application.add_exception_handler(AppError, app_error_handler)
    application.add_exception_handler(Exception, app_error_handler)
    application.add_exception_handler(RequestValidationError, validation_exception_handler)
    application.include_router(api_router)
    return application


app = create_app()
