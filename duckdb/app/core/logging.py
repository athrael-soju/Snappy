"""Logging utilities for the DuckDB analytics service."""

from __future__ import annotations

import logging
import sys

from app.core.config import settings


def setup_logging() -> logging.Logger:
    """Configure and return the root logger."""
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL, logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    return logging.getLogger("duckdb_service")


logger = setup_logging()
