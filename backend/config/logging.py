"""Centralized logging configuration for Snappy backend."""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.logging import RichHandler

try:
    from pythonjsonlogger import jsonlogger

    JSON_LOGGER_AVAILABLE = True
except ImportError:
    JSON_LOGGER_AVAILABLE = False


class SensitiveDataFilter(logging.Filter):
    """Filter to redact sensitive data from logs."""

    SENSITIVE_KEYS = {
        "password",
        "secret",
        "token",
        "key",
        "api_key",
        "access_key",
        "secret_key",
        "authorization",
        "cookie",
        "session",
    }

    def filter(self, record: logging.LogRecord) -> bool:
        """Filter log record and redact sensitive data."""
        # Redact in message if it's a dict
        if hasattr(record, "msg") and isinstance(record.msg, dict):
            record.msg = self._redact_dict(record.msg)

        # Redact in args if present
        if hasattr(record, "args") and isinstance(record.args, dict):
            record.args = self._redact_dict(record.args)

        return True

    def _redact_dict(self, data: dict) -> dict:
        """Recursively redact sensitive keys in dictionary."""
        redacted = {}
        for key, value in data.items():
            key_lower = str(key).lower()
            if any(sensitive in key_lower for sensitive in self.SENSITIVE_KEYS):
                redacted[key] = "***REDACTED***"
            elif isinstance(value, dict):
                redacted[key] = self._redact_dict(value)
            elif isinstance(value, list):
                redacted[key] = [
                    self._redact_dict(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                redacted[key] = value
        return redacted


class RequestContextFilter(logging.Filter):
    """Add request context to log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Add request_id to record if not present."""
        if not hasattr(record, "request_id"):
            record.request_id = "-"
        return True


def setup_logging(
    log_level: str = "INFO",
    enable_json: bool = False,
    log_file: Optional[Path] = None,
    enable_rich: bool = True,
) -> None:
    """Configure application logging with structured output.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        enable_json: Enable JSON structured logging (recommended for production)
        log_file: Optional file path for log output with rotation
        enable_rich: Enable Rich console formatting (default: True for development)
    """
    level = getattr(logging, log_level.upper(), logging.INFO)

    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Console handler
    if enable_json and JSON_LOGGER_AVAILABLE:
        # JSON format for production (parseable by log aggregators)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        json_formatter = jsonlogger.JsonFormatter(
            "%(asctime)s %(levelname)s %(name)s %(funcName)s %(lineno)d %(request_id)s %(message)s",
            rename_fields={
                "levelname": "level",
                "asctime": "timestamp",
                "name": "logger",
                "funcName": "function",
            },
        )
        console_handler.setFormatter(json_formatter)
    elif enable_rich:
        # Rich handler for colorful development output
        console = Console(force_terminal=True)
        console_handler = RichHandler(
            console=console,
            show_time=True,
            show_path=False,
            rich_tracebacks=True,
            tracebacks_show_locals=False,
            markup=True,
        )
        console_handler.setLevel(level)
        # Simple format - Rich handles the rest
        console_handler.setFormatter(logging.Formatter("%(message)s"))
    else:
        if enable_json and not JSON_LOGGER_AVAILABLE:
            print(
                "WARNING: JSON logging requested but python-json-logger not installed. "
                "Falling back to text format.",
                file=sys.stderr,
            )

        # Human-readable format for development (fallback)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(request_id)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        console_handler.setFormatter(formatter)

    # Add filters
    console_handler.addFilter(SensitiveDataFilter())
    console_handler.addFilter(RequestContextFilter())
    root_logger.addHandler(console_handler)

    # File handler with rotation (optional) - always uses plain text format
    if log_file:
        log_file_path = Path(log_file)
        log_file_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.handlers.RotatingFileHandler(
            log_file_path,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
        )
        file_handler.setLevel(level)

        if enable_json and JSON_LOGGER_AVAILABLE:
            file_handler.setFormatter(json_formatter)
        else:
            # Plain text format for file logs
            file_formatter = logging.Formatter(
                fmt="%(asctime)s | %(request_id)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            file_handler.setFormatter(file_formatter)

        file_handler.addFilter(SensitiveDataFilter())
        file_handler.addFilter(RequestContextFilter())
        root_logger.addHandler(file_handler)

    # Configure third-party loggers to reduce noise
    logging.getLogger("uvicorn").setLevel(level)
    logging.getLogger("uvicorn.access").setLevel(
        logging.WARNING if level < logging.WARNING else level
    )
    logging.getLogger("uvicorn.error").setLevel(level)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("minio").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    # Log startup info
    logger = logging.getLogger(__name__)
    logger.info(
        "Logging configured: level=%s, json=%s, rich=%s, file=%s",
        log_level,
        enable_json,
        enable_rich and not enable_json,
        str(log_file) if log_file else "disabled",
    )
