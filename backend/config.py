"""
Configuration module for FastAPI backend.

All settings are dynamically loaded from runtime configuration.
Values can be updated at runtime via the configuration API.
See docs/configuration.md for detailed documentation of all options.
"""

import os
from typing import Any
from dotenv import load_dotenv
from runtime_config import get_runtime_config

load_dotenv()

# Initialize runtime config with environment variables
_runtime = get_runtime_config()

# Configuration defaults for each setting
_CONFIG_DEFAULTS = {
    # Application
    "LOG_LEVEL": ("str", "INFO"),
    "ALLOWED_ORIGINS": ("list", "*"),
    
    # Processing
    "DEFAULT_TOP_K": ("int", 5),
    "MAX_TOKENS": ("int", 500),
    "BATCH_SIZE": ("int", 12),
    "WORKER_THREADS": ("int", 8),
    "ENABLE_PIPELINE_INDEXING": ("bool", True),
    "MAX_CONCURRENT_BATCHES": ("int", 3),
    
    # ColPali API
    "COLPALI_MODE": ("str", "gpu"),
    "COLPALI_CPU_URL": ("str", "http://localhost:7001"),
    "COLPALI_GPU_URL": ("str", "http://localhost:7002"),
    "COLPALI_API_BASE_URL": ("str", ""),
    "COLPALI_API_TIMEOUT": ("int", 300),
    
    # Qdrant
    "QDRANT_URL": ("str", "http://localhost:6333"),
    "QDRANT_COLLECTION_NAME": ("str", "documents"),
    "QDRANT_SEARCH_LIMIT": ("int", 20),
    "QDRANT_PREFETCH_LIMIT": ("int", 200),
    "QDRANT_ON_DISK": ("bool", True),
    "QDRANT_ON_DISK_PAYLOAD": ("bool", True),
    "QDRANT_USE_BINARY": ("bool", False),
    "QDRANT_BINARY_ALWAYS_RAM": ("bool", True),
    "QDRANT_SEARCH_IGNORE_QUANT": ("bool", False),
    "QDRANT_SEARCH_RESCORE": ("bool", True),
    "QDRANT_SEARCH_OVERSAMPLING": ("float", 2.0),
    "QDRANT_MEAN_POOLING_ENABLED": ("bool", False),
    
    # MUVERA
    "MUVERA_ENABLED": ("bool", False),
    "MUVERA_K_SIM": ("int", 6),
    "MUVERA_DIM_PROJ": ("int", 32),
    "MUVERA_R_REPS": ("int", 20),
    "MUVERA_RANDOM_SEED": ("int", 42),
    
    # MinIO
    "MINIO_URL": ("str", "http://localhost:9000"),
    "MINIO_PUBLIC_URL": ("str", "http://localhost:9000"),
    "MINIO_ACCESS_KEY": ("str", "minioadmin"),
    "MINIO_SECRET_KEY": ("str", "minioadmin"),
    "MINIO_BUCKET_NAME": ("str", "documents"),
    "MINIO_WORKERS": ("int", 12),
    "MINIO_RETRIES": ("int", 3),
    "MINIO_FAIL_FAST": ("bool", False),
    "MINIO_PUBLIC_READ": ("bool", True),
    "MINIO_IMAGE_FMT": ("str", "JPEG"),
    "MINIO_IMAGE_QUALITY": ("int", 75),
}


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
            elif name == "COLPALI_API_BASE_URL" and not value:
                mode = __getattr__("COLPALI_MODE")
                return __getattr__("COLPALI_GPU_URL") if mode == "gpu" else __getattr__("COLPALI_CPU_URL")
            elif name == "MINIO_PUBLIC_URL" and not value:
                return __getattr__("MINIO_URL")
            return value
    
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
