from __future__ import annotations

import logging
from functools import lru_cache
from threading import Lock
from typing import Optional

import config
from clients.colpali import ColPaliClient
from clients.duckdb import DuckDBClient
from clients.minio import MinioClient
from clients.ocr import OcrClient
from clients.qdrant import QdrantClient

logger = logging.getLogger(__name__)


class ServiceInitError:
    """Tracks service initialization errors thread-safely."""

    def __init__(self):
        self._error: Optional[str] = None
        self._lock = Lock()

    def set(self, error: str):
        """Set the error message."""
        with self._lock:
            self._error = error

    def clear(self):
        """Clear the error message."""
        with self._lock:
            self._error = None

    def get(self) -> Optional[str]:
        """Get the current error message."""
        with self._lock:
            return self._error


# Thread-safe error tracking
colpali_init_error = ServiceInitError()
qdrant_init_error = ServiceInitError()
minio_init_error = ServiceInitError()
ocr_init_error = ServiceInitError()
duckdb_init_error = ServiceInitError()


@lru_cache(maxsize=1)
def _get_colpali_client_cached() -> ColPaliClient:
    return ColPaliClient()


def get_colpali_client() -> ColPaliClient:
    """Return the cached ColPali service instance, capturing initialization errors."""
    try:
        service = _get_colpali_client_cached()
        colpali_init_error.clear()
        return service
    except Exception as exc:
        logger.error("Failed to initialize ColPali service: %s", exc)
        colpali_init_error.set(str(exc))
        _get_colpali_client_cached.cache_clear()
        raise


class _ColPaliClientProxy:
    """Proxy to preserve existing attribute-style access to the ColPali client."""

    def __getattr__(self, name: str):
        return getattr(get_colpali_client(), name)


api_client = _ColPaliClientProxy()


@lru_cache(maxsize=1)
def _get_ocr_service_cached() -> OcrClient:
    """Create and cache OcrClient instance."""
    if not config.DEEPSEEK_OCR_ENABLED:
        raise RuntimeError("DeepSeek OCR service is disabled in configuration")

    minio_service = get_minio_service()
    duckdb_service = get_duckdb_service() if config.DUCKDB_ENABLED else None

    return OcrClient(
        minio_service=minio_service,
        duckdb_service=duckdb_service,
    )


def get_ocr_service() -> Optional[OcrClient]:
    """Return the cached OCR service if enabled."""
    if not config.DEEPSEEK_OCR_ENABLED:
        ocr_init_error.set("OCR service disabled in configuration")
        return None

    try:
        service = _get_ocr_service_cached()
        ocr_init_error.clear()
        return service
    except Exception as exc:
        logger.error("Failed to initialize OCR service: %s", exc)
        ocr_init_error.set(str(exc))
        _get_ocr_service_cached.cache_clear()
        return None


@lru_cache(maxsize=1)
def _get_duckdb_service_cached() -> DuckDBClient:
    """Create and cache DuckDBClient instance."""
    if not config.DUCKDB_ENABLED:
        raise RuntimeError("DuckDB service is disabled in configuration")

    return DuckDBClient()


def get_duckdb_service() -> Optional[DuckDBClient]:
    """Return the cached DuckDB service if enabled."""
    if not config.DUCKDB_ENABLED:
        duckdb_init_error.set("DuckDB service disabled in configuration")
        return None

    try:
        service = _get_duckdb_service_cached()
        duckdb_init_error.clear()
        return service
    except Exception as exc:
        logger.error("Failed to initialize DuckDB service: %s", exc)
        duckdb_init_error.set(str(exc))
        _get_duckdb_service_cached.cache_clear()
        return None


@lru_cache(maxsize=1)
def _get_minio_service_cached() -> MinioClient:
    return MinioClient()


def get_minio_service() -> MinioClient:
    """Return the cached MinIO service, capturing initialization errors."""
    try:
        service = _get_minio_service_cached()
        minio_init_error.clear()
        return service
    except Exception as exc:  # pragma: no cover - defensive guard
        logger.error("Failed to initialize MinIO service: %s", exc)
        minio_init_error.set(str(exc))
        _get_minio_service_cached.cache_clear()
        raise


@lru_cache(maxsize=1)
def _get_qdrant_service_cached() -> QdrantClient:
    minio_service = get_minio_service()

    ocr_service = None
    if config.DEEPSEEK_OCR_ENABLED:
        ocr_service = get_ocr_service()
        if ocr_service is None:
            logger.warning("OCR is enabled but service failed to initialize")

    return QdrantClient(
        api_client=get_colpali_client(),
        minio_service=minio_service,
        ocr_service=ocr_service,
    )


def get_qdrant_service() -> Optional[QdrantClient]:
    """Return the cached Qdrant service, capturing initialization errors."""
    try:
        service = _get_qdrant_service_cached()
        qdrant_init_error.clear()
        return service
    except Exception as exc:  # pragma: no cover - defensive guard
        logger.error("Failed to initialize Qdrant service: %s", exc)
        qdrant_init_error.set(str(exc))
        _get_qdrant_service_cached.cache_clear()
        return None


def invalidate_services():
    """Invalidate cached services so they are recreated on next access."""
    logger.info("Invalidating cached services to apply new configuration")

    # Close existing service instances before clearing caches to prevent resource leaks
    try:
        # Close DuckDB service session
        if _get_duckdb_service_cached.cache_info().currsize > 0:
            try:
                service = _get_duckdb_service_cached()
                if hasattr(service, "close"):
                    service.close()
            except Exception as e:
                logger.warning(f"Error closing DuckDB service during invalidation: {e}")
    except Exception as e:
        logger.warning(f"Error accessing cached services for cleanup: {e}")

    # Clear error states
    colpali_init_error.clear()
    qdrant_init_error.clear()
    minio_init_error.clear()
    ocr_init_error.clear()
    duckdb_init_error.clear()

    # Clear caches
    _get_qdrant_service_cached.cache_clear()
    _get_minio_service_cached.cache_clear()
    _get_colpali_client_cached.cache_clear()
    _get_ocr_service_cached.cache_clear()
    _get_duckdb_service_cached.cache_clear()
