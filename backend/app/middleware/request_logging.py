import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("app.request")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        start = time.perf_counter()
        client = request.client.host if request.client else "-"
        query = f"?{request.url.query}" if request.url.query else ""

        try:
            response = await call_next(request)
        except Exception:
            duration_ms = (time.perf_counter() - start) * 1000
            logger.exception(
                "%s %s%s | client=%s | failed in %.1fms",
                request.method,
                request.url.path,
                query,
                client,
                duration_ms,
            )
            raise

        duration_ms = (time.perf_counter() - start) * 1000
        log = logger.warning if response.status_code >= 400 else logger.info
        log(
            "%s %s%s -> %s | client=%s | %.1fms",
            request.method,
            request.url.path,
            query,
            response.status_code,
            client,
            duration_ms,
        )
        return response
