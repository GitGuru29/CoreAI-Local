from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.api.error_handlers import app_error_handler, validation_exception_handler
from app.api.router import api_router
from app.core.config import get_settings
from app.core.logging import get_logger, setup_logging
from app.core.middleware import AccessLogMiddleware, ApiKeyAuthMiddleware
from app.services.auth import AuthService
from app.services.request_guard import RequestGuardService
from app.utils.errors import AppError

_settings = get_settings()
setup_logging(_settings.log_level, _settings.log_dir, _settings.log_file)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(application: FastAPI):
    settings = get_settings()
    application.state.settings = settings
    application.state.http_client = httpx.AsyncClient()
    application.state.request_guard = RequestGuardService(
        max_requests=settings.rate_limit_requests,
        window_seconds=settings.rate_limit_window_seconds,
        max_concurrent_requests=settings.max_concurrent_ai_requests,
        acquire_timeout=settings.queue_wait_timeout,
    )
    logger.info(
        "Starting %s on %s:%s",
        settings.app_name,
        settings.api_host,
        settings.api_port,
    )
    if settings.auth_enabled:
        logger.info(
            "API key auth enabled for paths outside %s",
            settings.auth_exempt_path_list,
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
    if settings.cors_origin_list:
        application.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origin_list,
            allow_credentials=True,
            allow_methods=["GET", "POST", "OPTIONS"],
            allow_headers=["*"],
        )
    application.add_middleware(
        ApiKeyAuthMiddleware,
        auth_service=AuthService(
            enabled=settings.auth_enabled,
            api_key=settings.auth_api_key,
            exempt_paths=settings.auth_exempt_path_list,
        ),
    )
    application.add_middleware(AccessLogMiddleware)
    application.add_exception_handler(AppError, app_error_handler)
    application.add_exception_handler(Exception, app_error_handler)
    application.add_exception_handler(RequestValidationError, validation_exception_handler)
    application.include_router(api_router)
    return application


app = create_app()
