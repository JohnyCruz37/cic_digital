from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from cic_digital.core.exceptions import AppException
from cic_digital.core.logger import get_logger
from cic_digital.schemas.response import ErrorDetail, ErrorResponse

logger = get_logger(__name__)


def _error_payload(code: str, message: str, details: dict | None = None) -> dict:
    return ErrorResponse(
        error=ErrorDetail(code=code, message=message, details=details),
    ).model_dump()


async def app_exception_handler(_request: Request, exc: AppException) -> JSONResponse:
    logger.warning("AppException [%s]: %s", exc.code, exc.message)
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_payload(exc.code, exc.message),
    )


async def http_exception_handler(
    _request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_payload("http_error", str(exc.detail)),
    )


async def validation_exception_handler(
    _request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=_error_payload(
            "validation_error",
            "Erro de validação nos dados enviados",
            details={"errors": exc.errors()},
        ),
    )


async def unhandled_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Erro não tratado: %s", exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=_error_payload("internal_error", "Erro interno do servidor"),
    )
