"""
Configuration module for FastAPI backend.

All settings are dynamically loaded from runtime configuration.
Values can be updated at runtime via the configuration API.
Defaults and types are defined in config_schema.py (single source of truth).
"""

import os
import re
from typing import Any

from config_schema import get_config_defaults
from dotenv import load_dotenv
from runtime_config import get_runtime_config

load_dotenv()

# Initialize runtime config with environment variables
_runtime = get_runtime_config()

# Get configuration defaults from schema (single source of truth)
_CONFIG_DEFAULTS = get_config_defaults()


def _slugify_bucket_name(name: str) -> str:
    sanitized = re.sub(r"[^a-z0-9-]+", "-", name.lower())
    sanitized = re.sub(r"-{2,}", "-", sanitized).strip("-")
    return sanitized or "documents"


def _get_auto_bucket_name() -> str:
    base = __getattr__("QDRANT_COLLECTION_NAME")
    return _slugify_bucket_name(base)


def _get_auto_minio_workers() -> int:
    cpu = os.cpu_count() or 4
    if cpu <= 4:
        base = 4
    elif cpu <= 8:
        base = 6
    elif cpu <= 16:
        base = 10
    else:
        base = 14
    concurrency = get_pipeline_max_concurrency()
    workers = base + max(0, concurrency - 1) * 2
    return max(4, min(32, workers))


def _get_auto_minio_retries(workers: int) -> int:
    if workers >= 24:
        return 5
    if workers >= 16:
        return 4
    if workers >= 8:
        return 3
    return 2


def __getattr__(name: str) -> Any:
    """
    Dynamically retrieve configuration values.
    This allows config values to be accessed like module constants but read from runtime config.
    """
    if name in _CONFIG_DEFAULTS:
        type_str, default = _CONFIG_DEFAULTS[name]

        if type_str == "int":
            if name == "MINIO_WORKERS":
                if _runtime.has(name):
                    return _runtime.get_int(name, default)
                return _get_auto_minio_workers()
            if name == "MINIO_RETRIES":
                if _runtime.has(name):
                    return _runtime.get_int(name, default)
                workers = __getattr__("MINIO_WORKERS")
                return _get_auto_minio_retries(workers)
            return _runtime.get_int(name, default)
        elif type_str == "float":
            return _runtime.get_float(name, default)
        elif type_str == "bool":
            return _runtime.get_bool(name, default)
        elif type_str == "list":
            raw = _runtime.get(name, str(default))
            if raw.strip() == "*":
                return ["*"]
            return [o.strip() for o in raw.split(",") if o.strip()]
        else:  # str
            value = _runtime.get(name, str(default))
            # Handle special cases
            if name == "COLPALI_MODE":
                return value.lower()
            if name == "MINIO_PUBLIC_URL" and not value:
                return __getattr__("MINIO_URL")
            if name == "MINIO_BUCKET_NAME" and not value.strip():
                return _get_auto_bucket_name()
            return value

    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


def get_ingestion_worker_threads() -> int:
    """Heuristic for PDF conversion worker threads based on CPU count."""
    cpu = os.cpu_count() or 4
    return max(2, min(8, cpu))


def get_pipeline_max_concurrency() -> int:
    """Estimate concurrent pipeline batches based on hardware and batch size."""
    if not __getattr__("ENABLE_PIPELINE_INDEXING"):
        return 1
    batch_size = max(1, __getattr__("BATCH_SIZE"))
    cpu = os.cpu_count() or 4
    # Aim for at least 2 workers when batches are large enough and hardware permits
    base = 1 if batch_size < 4 else 2
    workers = max(base, min(4, cpu // 2))
    return max(1, workers)
