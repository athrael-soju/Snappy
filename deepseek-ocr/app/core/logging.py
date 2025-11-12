"""
Logging configuration for DeepSeek OCR service.
"""

import logging
import sys


class RequestContextFilter(logging.Filter):
    """Add request context to log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Add request_id to record if not present."""
        if not hasattr(record, "request_id"):
            record.request_id = "-"
        return True


def setup_logging() -> logging.Logger:
    """Configure and return application logger."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(request_id)s | %(levelname)-8s | %(name)s | %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    # Add request context filter to all handlers
    for handler in logging.root.handlers:
        handler.addFilter(RequestContextFilter())

    return logging.getLogger("deepseek_ocr")


logger = setup_logging()
