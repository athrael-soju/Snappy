"""Logging configuration with request ID support."""

import logging


class RequestContextFilter(logging.Filter):
    """Add request context to log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Add request_id to record if not present."""
        if not hasattr(record, "request_id"):
            record.request_id = "-"
        return True


def setup_logging():
    """Configure logging with request context support."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(request_id)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Add request context filter to root logger
    for handler in logging.root.handlers:
        handler.addFilter(RequestContextFilter())


# Global logger instance
logger = logging.getLogger(__name__)
