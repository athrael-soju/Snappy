import os
from typing import Final
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ===== Application Settings =====
# Core Application
LOG_LEVEL: Final[str] = os.getenv("LOG_LEVEL", "INFO")

# Processing
DEFAULT_TOP_K: Final[int] = int(os.getenv("DEFAULT_TOP_K", "5"))
MAX_TOKENS: Final[int] = int(os.getenv("MAX_TOKENS", "500"))
BATCH_SIZE: Final[int] = int(os.getenv("BATCH_SIZE", "4"))
WORKER_THREADS: Final[int] = int(os.getenv("WORKER_THREADS", "4"))

# ===== AI/ML Configuration =====
# OpenAI
OPENAI_API_KEY: Final[str] = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL: Final[str] = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

# Embedding Model (for reference - actual model runs in separate service)
MODEL_NAME: Final[str] = os.getenv("MODEL_NAME", "nomic-ai/colnomic-embed-multimodal-3b")
COLPALI_SERVICE_URL: Final[str] = os.getenv("COLPALI_SERVICE_URL", "http://localhost:8000")

# ===== Storage Configurations =====
# Qdrant
QDRANT_URL: Final[str] = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_COLLECTION_NAME: Final[str] = os.getenv("QDRANT_COLLECTION_NAME", "documents")
QDRANT_SEARCH_LIMIT: Final[int] = int(os.getenv("QDRANT_SEARCH_LIMIT", "20"))
QDRANT_PREFETCH_LIMIT: Final[int] = int(os.getenv("QDRANT_PREFETCH_LIMIT", "200"))

# MinIO Object Storage
MINIO_URL: Final[str] = os.getenv("MINIO_URL", "http://localhost:9000")
MINIO_ACCESS_KEY: Final[str] = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY: Final[str] = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET_NAME: Final[str] = os.getenv("MINIO_BUCKET_NAME", "documents")

