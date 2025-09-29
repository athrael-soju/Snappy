"""
Configuration module for FastAPI backend.

All settings are loaded from environment variables.
See docs/configuration.md for detailed documentation of all options.
"""

import os
from typing import Final
from dotenv import load_dotenv

load_dotenv()


def _env_bool(name: str, default: str = "False") -> bool:
    """Parse environment boolean flags robustly."""
    return os.getenv(name, default).strip().lower() in ("1", "true", "yes", "on")


# Application
LOG_LEVEL: Final[str] = os.getenv("LOG_LEVEL", "INFO")
ALLOWED_ORIGINS_RAW: Final[str] = os.getenv("ALLOWED_ORIGINS", "*")
ALLOWED_ORIGINS: Final[list[str]] = (
    ["*"]
    if ALLOWED_ORIGINS_RAW.strip() == "*"
    else [o.strip() for o in ALLOWED_ORIGINS_RAW.split(",") if o.strip()]
)

# Processing
DEFAULT_TOP_K: Final[int] = int(os.getenv("DEFAULT_TOP_K", "5"))
MAX_TOKENS: Final[int] = int(os.getenv("MAX_TOKENS", "500"))
BATCH_SIZE: Final[int] = int(os.getenv("BATCH_SIZE", "4"))
WORKER_THREADS: Final[int] = int(os.getenv("WORKER_THREADS", "4"))
ENABLE_PIPELINE_INDEXING: Final[bool] = _env_bool("ENABLE_PIPELINE_INDEXING", "True")
MAX_CONCURRENT_BATCHES: Final[int] = int(os.getenv("MAX_CONCURRENT_BATCHES", "2"))
MINIO_IMAGE_QUALITY: Final[int] = int(os.getenv("MINIO_IMAGE_QUALITY", "90"))

# ColPali API
COLPALI_MODE: Final[str] = os.getenv("COLPALI_MODE", "cpu").lower()
COLPALI_CPU_URL: Final[str] = os.getenv("COLPALI_CPU_URL", "http://localhost:7001")
COLPALI_GPU_URL: Final[str] = os.getenv("COLPALI_GPU_URL", "http://localhost:7002")

_explicit_base = os.getenv("COLPALI_API_BASE_URL", "").strip()
if _explicit_base:
    COLPALI_API_BASE_URL: Final[str] = _explicit_base
else:
    COLPALI_API_BASE_URL: Final[str] = (
        COLPALI_GPU_URL if COLPALI_MODE == "gpu" else COLPALI_CPU_URL
    )

COLPALI_API_TIMEOUT: Final[int] = int(os.getenv("COLPALI_API_TIMEOUT", "300"))

# Qdrant
QDRANT_URL: Final[str] = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_COLLECTION_NAME: Final[str] = os.getenv("QDRANT_COLLECTION_NAME", "documents")
QDRANT_SEARCH_LIMIT: Final[int] = int(os.getenv("QDRANT_SEARCH_LIMIT", "20"))
QDRANT_PREFETCH_LIMIT: Final[int] = int(os.getenv("QDRANT_PREFETCH_LIMIT", "200"))
QDRANT_ON_DISK: Final[bool] = _env_bool("QDRANT_ON_DISK", "True")
QDRANT_ON_DISK_PAYLOAD: Final[bool] = _env_bool("QDRANT_ON_DISK_PAYLOAD", "True")
QDRANT_USE_BINARY: Final[bool] = _env_bool("QDRANT_USE_BINARY", "True")
QDRANT_BINARY_ALWAYS_RAM: Final[bool] = _env_bool("QDRANT_BINARY_ALWAYS_RAM", "True")
QDRANT_SEARCH_IGNORE_QUANT: Final[bool] = _env_bool("QDRANT_SEARCH_IGNORE_QUANT", "False")
QDRANT_SEARCH_RESCORE: Final[bool] = _env_bool("QDRANT_SEARCH_RESCORE", "True")
QDRANT_SEARCH_OVERSAMPLING: Final[float] = float(os.getenv("QDRANT_SEARCH_OVERSAMPLING", "2.0"))

# MUVERA
MUVERA_ENABLED: Final[bool] = _env_bool("MUVERA_ENABLED", "False")
MUVERA_K_SIM: Final[int] = int(os.getenv("MUVERA_K_SIM", "6"))
MUVERA_DIM_PROJ: Final[int] = int(os.getenv("MUVERA_DIM_PROJ", "32"))
MUVERA_R_REPS: Final[int] = int(os.getenv("MUVERA_R_REPS", "20"))
MUVERA_RANDOM_SEED: Final[int] = int(os.getenv("MUVERA_RANDOM_SEED", "42"))

# MinIO
MINIO_URL: Final[str] = os.getenv("MINIO_URL", "http://localhost:9000")
MINIO_PUBLIC_URL: Final[str] = os.getenv("MINIO_PUBLIC_URL", MINIO_URL)
MINIO_ACCESS_KEY: Final[str] = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY: Final[str] = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET_NAME: Final[str] = os.getenv("MINIO_BUCKET_NAME", "documents")
MINIO_WORKERS: Final[int] = int(os.getenv("MINIO_WORKERS", "4"))
MINIO_RETRIES: Final[int] = int(os.getenv("MINIO_RETRIES", "2"))
MINIO_FAIL_FAST: Final[bool] = _env_bool("MINIO_FAIL_FAST", "False")
MINIO_PUBLIC_READ: Final[bool] = _env_bool("MINIO_PUBLIC_READ", "True")
MINIO_IMAGE_FMT: Final[str] = os.getenv("MINIO_IMAGE_FMT", "PNG")
