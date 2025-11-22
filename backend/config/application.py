"""
Configuration module for FastAPI backend.

All settings are dynamically loaded from runtime configuration.
Values can be updated at runtime via the configuration API.
Defaults and types are defined in config_schema.py (single source of truth).
"""

import logging
import os
import re
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


def _slugify_bucket_name(name: str) -> str:
    sanitized = re.sub(r"[^a-z0-9-]+", "-", name.lower())
    sanitized = re.sub(r"-{2,}", "-", sanitized).strip("-")
    return sanitized or "documents"


def _get_auto_bucket_name() -> str:
    base = __getattr__("QDRANT_COLLECTION_NAME")
    return _slugify_bucket_name(base)


def _get_auto_minio_workers() -> int:
    """Auto-calculate MinIO workers with safety checks."""
    try:
        cpu = os.cpu_count() or 4
        if cpu <= 4:
            base = 4
        elif cpu <= 8:
            base = 6
        elif cpu <= 16:
            base = 10
        else:
            base = 14

        # Safely get concurrency without circular calls
        try:
            concurrency = get_pipeline_max_concurrency()
        except (AttributeError, RecursionError) as e:
            logger.warning(
                f"Could not determine pipeline concurrency: {e}, using default"
            )
            concurrency = 1

        workers = base + max(0, concurrency - 1) * 2
        return max(4, min(32, workers))
    except Exception as e:
        logger.error(f"Error calculating MINIO_WORKERS: {e}, using default")
        return 4


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
    # Handle auto-sized values that were removed from schema
    if name == "MINIO_WORKERS":
        return _get_auto_minio_workers()
    if name == "MINIO_RETRIES":
        workers = __getattr__("MINIO_WORKERS")
        return _get_auto_minio_retries(workers)

    # Handle hard-coded constants
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
            value = _runtime.get(name, str(default))
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
    try:
        # Auto-config is always enabled for optimal performance
        batch_size = max(1, __getattr__("BATCH_SIZE"))
        cpu = os.cpu_count() or 4
        # Aim for at least 2 workers when batches are large enough and hardware permits
        base = 1 if batch_size < 4 else 2
        workers = max(base, min(4, cpu // 2))
        return max(1, workers)
    except (AttributeError, RecursionError) as e:
        logger.warning(
            f"Error determining pipeline max concurrency: {e}, using default"
        )
        return 1


# Hard-coded optimized Qdrant settings (always on for best performance)
QDRANT_USE_BINARY = True  # Binary quantization (32x memory reduction)
QDRANT_BINARY_ALWAYS_RAM = True  # Keep binary vectors in RAM
QDRANT_SEARCH_RESCORE = True  # Rescore with full precision
QDRANT_SEARCH_OVERSAMPLING = 2.0  # Oversampling factor
QDRANT_SEARCH_IGNORE_QUANT = False  # Never ignore quantization
QDRANT_MEAN_POOLING_ENABLED = True  # Always use mean pooling for better recall
QDRANT_PREFETCH_LIMIT = 200  # Prefetch candidates for re-ranking
QDRANT_ON_DISK = True  # Store vectors on disk (memory optimization)
QDRANT_ON_DISK_PAYLOAD = True  # Store payload on disk

# Hard-coded MinIO settings (auto-sized or optimized defaults)
MINIO_FAIL_FAST = False  # Resilient by default
IMAGE_FORMAT = "JPEG"  # Best compression/quality balance
IMAGE_QUALITY = 75  # Good quality/size balance

# Hard-coded DeepSeek OCR settings (auto-sized or optimized defaults)
DEEPSEEK_OCR_API_TIMEOUT = 180  # 3 minutes - balances speed and reliability
DEEPSEEK_OCR_MAX_WORKERS = 4  # Good default for single GPU
DEEPSEEK_OCR_POOL_SIZE = 20  # Sufficient for retry handling
DEEPSEEK_OCR_INCLUDE_GROUNDING = True  # Always include bounding boxes
DEEPSEEK_OCR_INCLUDE_IMAGES = True  # Always extract embedded images
DEEPSEEK_OCR_LOCATE_TEXT = ""  # Empty by default
DEEPSEEK_OCR_CUSTOM_PROMPT = ""  # Empty by default

# Hard-coded upload settings (optimized defaults)
UPLOAD_CHUNK_SIZE_MBYTES = 2.0  # 2MB chunks balance throughput and memory
UPLOAD_MAX_WORKERS = 4  # Good default for I/O-bound operations
