"""
Configuration module for FastAPI backend.

All settings are dynamically loaded from runtime configuration.
Values can be updated at runtime via the configuration API.
Defaults and types are defined in config_schema.py (single source of truth).
"""

import os
from typing import Any
from dotenv import load_dotenv
from runtime_config import get_runtime_config
from config_schema import get_config_defaults

load_dotenv()

# Initialize runtime config with environment variables
_runtime = get_runtime_config()

# Get configuration defaults from schema (single source of truth)
_CONFIG_DEFAULTS = get_config_defaults()


def __getattr__(name: str) -> Any:
    """
    Dynamically retrieve configuration values.
    This allows config values to be accessed like module constants but read from runtime config.
    """
    if name in _CONFIG_DEFAULTS:
        type_str, default = _CONFIG_DEFAULTS[name]
        
        if type_str == "int":
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
            elif name == "MINIO_PUBLIC_URL" and not value:
                return __getattr__("MINIO_URL")
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
