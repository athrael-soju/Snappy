from __future__ import annotations

import logging
from functools import lru_cache
from typing import Optional

import config
from services.colpali import ColPaliService
from services.duckdb import DuckDBService
from services.minio import MinioService
from services.ocr import OcrService
from services.qdrant import QdrantService

logger = logging.getLogger(__name__)

colpali_init_error: Optional[str] = None
qdrant_init_error: Optional[str] = None
minio_init_error: Optional[str] = None
ocr_init_error: Optional[str] = None
duckdb_init_error: Optional[str] = None


@lru_cache(maxsize=1)
def _get_colpali_client_cached() -> ColPaliService:
    return ColPaliService()


def get_colpali_client() -> ColPaliService:
    """Return the cached ColPali service instance, capturing initialization errors."""
    global colpali_init_error
    try:
        service = _get_colpali_client_cached()
        colpali_init_error = None
        return service
    except Exception as exc:
        logger.error("Failed to initialize ColPali service: %s", exc)
        colpali_init_error = str(exc)
        _get_colpali_client_cached.cache_clear()
        raise


class _ColPaliClientProxy:
    """Proxy to preserve existing attribute-style access to the ColPali client."""

    def __getattr__(self, name: str):
        return getattr(get_colpali_client(), name)


api_client = _ColPaliClientProxy()


@lru_cache(maxsize=1)
def _get_ocr_service_cached() -> OcrService:
    """Create and cache OcrService instance."""
    if not config.DEEPSEEK_OCR_ENABLED:
        raise RuntimeError("DeepSeek OCR service is disabled in configuration")

    minio_service = get_minio_service()
    duckdb_service = get_duckdb_service() if config.DUCKDB_ENABLED else None

    return OcrService(
        minio_service=minio_service,
        duckdb_service=duckdb_service,
    )


def get_ocr_service() -> Optional[OcrService]:
    """Return the cached OCR service if enabled."""
    global ocr_init_error

    if not config.DEEPSEEK_OCR_ENABLED:
        ocr_init_error = "OCR service disabled in configuration"
        return None

    try:
        service = _get_ocr_service_cached()
        ocr_init_error = None
        return service
    except Exception as exc:
        logger.error("Failed to initialize OCR service: %s", exc)
        ocr_init_error = str(exc)
        _get_ocr_service_cached.cache_clear()
        return None


@lru_cache(maxsize=1)
def _get_duckdb_service_cached() -> DuckDBService:
    """Create and cache DuckDBService instance."""
    if not config.DUCKDB_ENABLED:
        raise RuntimeError("DuckDB service is disabled in configuration")

    return DuckDBService()


def get_duckdb_service() -> Optional[DuckDBService]:
    """Return the cached DuckDB service if enabled."""
    global duckdb_init_error

    if not config.DUCKDB_ENABLED:
        duckdb_init_error = "DuckDB service disabled in configuration"
        return None

    try:
        service = _get_duckdb_service_cached()
        duckdb_init_error = None
        return service
    except Exception as exc:
        logger.error("Failed to initialize DuckDB service: %s", exc)
        duckdb_init_error = str(exc)
        _get_duckdb_service_cached.cache_clear()
        return None


@lru_cache(maxsize=1)
def _get_minio_service_cached() -> MinioService:
    return MinioService()


def get_minio_service() -> MinioService:
    """Return the cached MinIO service, capturing initialization errors."""
    global minio_init_error
    try:
        service = _get_minio_service_cached()
        minio_init_error = None
        return service
    except Exception as exc:  # pragma: no cover - defensive guard
        logger.error("Failed to initialize MinIO service: %s", exc)
        minio_init_error = str(exc)
        _get_minio_service_cached.cache_clear()
        raise


@lru_cache(maxsize=1)
def _get_qdrant_service_cached() -> QdrantService:
    minio_service = get_minio_service()

    ocr_service = None
    if config.DEEPSEEK_OCR_ENABLED:
        ocr_service = get_ocr_service()
        if ocr_service is None:
            logger.warning("OCR is enabled but service failed to initialize")

    return QdrantService(
        api_client=get_colpali_client(),
        minio_service=minio_service,
        ocr_service=ocr_service,
    )


def get_qdrant_service() -> Optional[QdrantService]:
    """Return the cached Qdrant service, capturing initialization errors."""
    global qdrant_init_error
    try:
        service = _get_qdrant_service_cached()
        qdrant_init_error = None
        return service
    except Exception as exc:  # pragma: no cover - defensive guard
        logger.error("Failed to initialize Qdrant service: %s", exc)
        qdrant_init_error = str(exc)
        _get_qdrant_service_cached.cache_clear()
        return None


def invalidate_services():
    """Invalidate cached services so they are recreated on next access."""
    global colpali_init_error, qdrant_init_error, minio_init_error, ocr_init_error, duckdb_init_error
    logger.info("Invalidating cached services to apply new configuration")
    colpali_init_error = None
    qdrant_init_error = None
    minio_init_error = None
    ocr_init_error = None
    duckdb_init_error = None
    _get_qdrant_service_cached.cache_clear()
    _get_minio_service_cached.cache_clear()
    _get_colpali_client_cached.cache_clear()
    _get_ocr_service_cached.cache_clear()
    _get_duckdb_service_cached.cache_clear()
