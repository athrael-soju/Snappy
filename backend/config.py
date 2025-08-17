import os
from typing import Final
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Helpers
def _env_bool(name: str, default: str = "False") -> bool:
    """Parse environment boolean flags robustly."""
    return os.getenv(name, default).strip().lower() in ("1", "true", "yes", "on")

# ===== Application Settings =====
# Core Application
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

# ===== AI/ML Configuration =====
# OpenAI
OPENAI_API_KEY: Final[str] = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL: Final[str] = os.getenv("OPENAI_MODEL", "gpt-5-nano")
OPENAI_TEMPERATURE: Final[float] = float(os.getenv("OPENAI_TEMPERATURE", "1.0"))
OPENAI_SYSTEM_PROMPT: Final[str] = os.getenv(
    "OPENAI_SYSTEM_PROMPT",
    "You are a helpful PDF assistant. Use only the provided page images "
    "to answer the user's question. If the answer isn't contained in the pages, "
    "say you cannot find it. Be concise and always mention from which pages the answer is taken.",
)

"""
ColPali API configuration

Priority:
1) If COLPALI_API_BASE_URL is explicitly set, use it as-is.
2) Otherwise, select based on COLPALI_MODE (cpu|gpu) between COLPALI_CPU_URL and COLPALI_GPU_URL.
"""

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

# ===== Storage Configurations =====
# Qdrant
QDRANT_URL: Final[str] = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_COLLECTION_NAME: Final[str] = os.getenv("QDRANT_COLLECTION_NAME", "documents")
QDRANT_SEARCH_LIMIT: Final[int] = int(os.getenv("QDRANT_SEARCH_LIMIT", "20"))
QDRANT_PREFETCH_LIMIT: Final[int] = int(os.getenv("QDRANT_PREFETCH_LIMIT", "200"))

# MinIO Object Storage
MINIO_URL: Final[str] = os.getenv("MINIO_URL", "http://localhost:9000")
MINIO_PUBLIC_URL: Final[str] = os.getenv("MINIO_PUBLIC_URL", MINIO_URL)
MINIO_ACCESS_KEY: Final[str] = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY: Final[str] = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET_NAME: Final[str] = os.getenv("MINIO_BUCKET_NAME", "documents")
MINIO_WORKERS: Final[int] = int(os.getenv("MINIO_WORKERS", "4"))
MINIO_RETRIES: Final[int] = int(os.getenv("MINIO_RETRIES", "2"))
MINIO_FAIL_FAST: Final[bool] = _env_bool("MINIO_FAIL_FAST", "False")
MINIO_PUBLIC_READ: Final[bool] = _env_bool("MINIO_PUBLIC_READ", "True")
MINIO_IMAGE_FMT: Final[str] = os.getenv("MINIO_IMAGE_FMT", "JPEG")
