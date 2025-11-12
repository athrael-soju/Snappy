"""Configuration management for the DuckDB analytics service."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class Settings:
    """Application settings loaded from environment variables."""

    DUCKDB_DATABASE_PATH: str = os.getenv(
        "DUCKDB_DATABASE_PATH", "./data/ocr_data.duckdb"
    )
    API_HOST: str = os.getenv("DUCKDB_API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("DUCKDB_API_PORT", "8300"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()
    API_VERSION: str = os.getenv("DUCKDB_API_VERSION", "1.1.0")


settings = Settings()
