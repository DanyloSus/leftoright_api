import time
import uuid

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = structlog.get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        correlation_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=correlation_id,
            method=request.method,
            path=request.url.path,
        )

        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            elapsed = time.perf_counter() - start
            logger.error("request_failed", duration_ms=round(elapsed * 1000, 2))
            raise

        elapsed = time.perf_counter() - start
        logger.info(
            "request_completed",
            status_code=response.status_code,
            duration_ms=round(elapsed * 1000, 2),
        )

        response.headers["X-Request-ID"] = correlation_id
        return response
