"""Request timing middleware for performance monitoring."""

import logging
import time

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class TimingMiddleware(BaseHTTPMiddleware):
    """Middleware that logs request duration for performance monitoring.

    Logs the following for each request:
    - HTTP method and path
    - Status code
    - Duration in seconds
    - Client IP address

    This helps identify slow endpoints and performance bottlenecks.
    """

    # Paths to exclude from timing logs (reduce noise)
    EXCLUDE_PATHS = {"/health", "/metrics", "/favicon.ico"}

    async def dispatch(self, request: Request, call_next):
        """Process request and log timing information."""
        start_time = time.perf_counter()

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration_s = time.perf_counter() - start_time

        # Skip logging for excluded paths to reduce noise
        if request.url.path not in self.EXCLUDE_PATHS:
            # Get client IP
            client_ip = None
            if request.client:
                client_ip = request.client.host

            # Log with structured data
            log_level = logging.INFO
            # Warn on slow requests (>1 second)
            if duration_s > 1.0:
                log_level = logging.WARNING

            logger.log(
                log_level,
                "%s %s - %d (%.2fs)",
                request.method,
                request.url.path,
                response.status_code,
                duration_s,
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_s": round(duration_s, 3),
                    "client_ip": client_ip,
                },
            )

        return response
