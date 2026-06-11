import time
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from cic_digital.core.logger import get_logger
from cic_digital.utils.correlation import generate_correlation_id

logger = get_logger(__name__)

CORRELATION_HEADER = "X-Correlation-ID"


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        correlation_id = request.headers.get(CORRELATION_HEADER) or generate_correlation_id()
        request.state.correlation_id = correlation_id

        start = time.perf_counter()
        logger.info(
            "Request started [%s] %s %s",
            correlation_id,
            request.method,
            request.url.path,
        )

        response = await call_next(request)

        duration_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "Request completed [%s] %s %s — %.2fms — status=%s",
            correlation_id,
            request.method,
            request.url.path,
            duration_ms,
            response.status_code,
        )

        response.headers[CORRELATION_HEADER] = correlation_id
        return response
