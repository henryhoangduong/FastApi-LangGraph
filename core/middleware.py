import time
from typing import Callable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from core.metrics import (db_connections, http_request_duration_seconds,
                          http_requests_total)


class MetricsMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()

        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception:
            status_code = 500
            raise
        finally:
            duration = time.time() - start_time

            # Record metrics
            http_requests_total.labels(
                method=request.method, endpoint=request.url.path, status=status_code).inc()

            http_request_duration_seconds.labels(
                method=request.method, endpoint=request.url.path).observe(duration)

        return response
