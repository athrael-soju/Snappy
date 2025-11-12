"""Request ID middleware for distributed tracing in ColPali service."""

import logging
import uuid
from contextvars import ContextVar

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

# Context variable to store request ID for the current async context
request_id_var: ContextVar[str] = ContextVar("request_id", default="-")


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware that adds unique request ID to all logs and responses."""

    async def dispatch(self, request: Request, call_next):
        """Process request and inject request ID into logging context."""
        # Extract existing request ID or generate new one
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request_id_var.set(request_id)

        # Store original log record factory
        old_factory = logging.getLogRecordFactory()

        def record_factory(*args, **kwargs):
            """Custom log record factory that adds request_id."""
            record = old_factory(*args, **kwargs)
            record.request_id = request_id_var.get()
            return record

        # Set custom factory for this request context
        logging.setLogRecordFactory(record_factory)

        try:
            # Process request
            response = await call_next(request)
            # Add request ID to response headers for client tracking
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            # Restore original factory
            logging.setLogRecordFactory(old_factory)


def get_request_id() -> str:
    """Get the current request ID from context."""
    return request_id_var.get()
