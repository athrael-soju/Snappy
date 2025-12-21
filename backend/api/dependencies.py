from __future__ import annotations

import logging
from functools import lru_cache
from threading import Lock
from typing import Optional

import config
from clients.colpali import ColPaliClient
from clients.local_storage import LocalStorageClient
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
storage_init_error = ServiceInitError()
ocr_init_error = ServiceInitError()


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

    storage_service = get_storage_service()

    return OcrClient(
        storage_service=storage_service,
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
def _get_storage_service_cached() -> LocalStorageClient:
    return LocalStorageClient()


def get_storage_service() -> LocalStorageClient:
    """Return the cached storage service, capturing initialization errors."""
    try:
        service = _get_storage_service_cached()
        storage_init_error.clear()
        return service
    except Exception as exc:  # pragma: no cover - defensive guard
        logger.error("Failed to initialize storage service: %s", exc)
        storage_init_error.set(str(exc))
        _get_storage_service_cached.cache_clear()
        raise




@lru_cache(maxsize=1)
def _get_qdrant_service_cached() -> QdrantClient:
    storage_service = get_storage_service()

    ocr_service = None
    if config.DEEPSEEK_OCR_ENABLED:
        ocr_service = get_ocr_service()
        if ocr_service is None:
            logger.warning("OCR is enabled but service failed to initialize")

    return QdrantClient(
        api_client=get_colpali_client(),
        storage_service=storage_service,
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
    logger.debug("Invalidating cached services to apply new configuration")

    # Close existing service instances before clearing caches to prevent resource leaks
    try:
        # No additional cleanup needed for current services
        pass
    except Exception as e:
        logger.warning(f"Error accessing cached services for cleanup: {e}")

    # Clear error states
    colpali_init_error.clear()
    qdrant_init_error.clear()
    storage_init_error.clear()
    ocr_init_error.clear()

    # Clear caches
    _get_qdrant_service_cached.cache_clear()
    _get_storage_service_cached.cache_clear()
    _get_colpali_client_cached.cache_clear()
    _get_ocr_service_cached.cache_clear()
