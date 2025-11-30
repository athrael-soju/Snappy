"""
Configuration module for FastAPI backend.

All settings are dynamically loaded from runtime configuration.
Values can be updated at runtime via the configuration API.
Defaults and types are defined in config_schema.py (single source of truth).
"""

import logging
import os
import threading
from typing import Any

from .schema import get_config_defaults
from dotenv import load_dotenv
from .runtime import get_runtime_config

load_dotenv()

# Initialize runtime config with environment variables
_runtime = get_runtime_config()

# Get configuration defaults from schema (single source of truth)
_CONFIG_DEFAULTS = get_config_defaults()

# Thread-safe recursion detection for __getattr__
_thread_local = threading.local()
_MAX_LOOKUP_DEPTH = 10

# Logger for config errors
logger = logging.getLogger(__name__)


def __getattr__(name: str) -> Any:
    """
    Dynamically retrieve configuration values with thread-safe recursion detection.
    This allows config values to be accessed like module constants but read from runtime config.
    """
    # Initialize thread-local depth if not present
    if not hasattr(_thread_local, "depth"):
        _thread_local.depth = 0

    # Detect excessive recursion (per-thread)
    if _thread_local.depth > _MAX_LOOKUP_DEPTH:
        raise RecursionError(
            f"Config lookup recursion detected for '{name}' (depth > {_MAX_LOOKUP_DEPTH})"
        )

    _thread_local.depth += 1
    try:
        return _getattr_impl(name)
    finally:
        _thread_local.depth -= 1


def _getattr_impl(name: str) -> Any:
    """Implementation of dynamic attribute lookup."""
    # Check module-level constants defined below
    if name in globals():
        value = globals()[name]
        # Only return if it's a constant (not a function or class)
        if not callable(value) and not name.startswith('_'):
            return value

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
            return _runtime.get(name, str(default))

    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


def get_ingestion_worker_threads() -> int:
    """Heuristic for PDF conversion worker threads based on CPU count."""
    cpu = os.cpu_count() or 4
    return max(2, min(8, cpu))


def get_pipeline_max_concurrency() -> int:
    """Estimate concurrent pipeline batches based on hardware and batch size."""
    try:
        batch_size = max(1, __getattr__("BATCH_SIZE"))
        cpu = os.cpu_count() or 4
        base = 1 if batch_size < 4 else 2
        workers = max(base, min(4, cpu // 2))
        return max(1, workers)
    except (AttributeError, RecursionError) as e:
        logger.warning(
            f"Error determining pipeline max concurrency: {e}, using default"
        )
        return 1


# Hard-coded Qdrant storage settings (not configurable via UI)
QDRANT_ON_DISK = True  # Store vectors on disk (memory optimization)
QDRANT_ON_DISK_PAYLOAD = True  # Store payload on disk

# Hard-coded image settings for inline storage
IMAGE_FORMAT = "WEBP"  # Best compression for inline storage (~25-35% smaller than JPEG)
IMAGE_QUALITY = 70  # Good quality/size balance for WebP

# Hard-coded DeepSeek OCR settings
DEEPSEEK_OCR_API_TIMEOUT = 180  # 3 minutes - balances speed and reliability
DEEPSEEK_OCR_POOL_SIZE = 20  # Sufficient for retry handling
DEEPSEEK_OCR_LOCATE_TEXT = ""  # Empty by default
DEEPSEEK_OCR_CUSTOM_PROMPT = ""  # Empty by default

# Hard-coded upload settings
UPLOAD_CHUNK_SIZE_MBYTES = 2.0  # 2MB chunks balance throughput and memory
