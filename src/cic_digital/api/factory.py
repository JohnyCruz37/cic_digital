from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from cic_digital.api.exception_handlers import (
    app_exception_handler,
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from cic_digital.api.middleware import RequestLoggingMiddleware
from cic_digital.api.router import api_router
from cic_digital.core.config import settings
from cic_digital.core.exceptions import AppException
from cic_digital.core.logger import get_logger
from cic_digital.db.connection import admin_db, db

logger = get_logger(__name__)


def create_app() -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        logger.info("Aplicação iniciada [env=%s]", settings.app_env)
        yield
        db.dispose()
        admin_db.dispose()
        logger.info("Aplicação encerrada")

    app = FastAPI(
        title=settings.api.title,
        description=settings.api.description,
        version=settings.api.version,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    app.add_middleware(RequestLoggingMiddleware)

    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

    app.include_router(api_router)
    return app
