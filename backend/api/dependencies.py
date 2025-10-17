from __future__ import annotations

import logging
from functools import lru_cache
from typing import Optional

import config
from services.colpali import ColPaliService
from services.minio import MinioService
from services.qdrant import MuveraPostprocessor, QdrantService

logger = logging.getLogger(__name__)

qdrant_init_error: Optional[str] = None
minio_init_error: Optional[str] = None


@lru_cache(maxsize=1)
def _get_colpali_client_cached() -> ColPaliService:
    return ColPaliService()


def get_colpali_client() -> ColPaliService:
    """Return the cached ColPali service instance."""
    return _get_colpali_client_cached()


class _ColPaliClientProxy:
    """Proxy to preserve existing attribute-style access to the ColPali client."""

    def __getattr__(self, name: str):
        return getattr(get_colpali_client(), name)


api_client = _ColPaliClientProxy()


@lru_cache(maxsize=1)
def _get_muvera_postprocessor_cached() -> Optional[MuveraPostprocessor]:
    if not config.MUVERA_ENABLED:
        return None

    info = get_colpali_client().get_info() or {}
    dim = int(info.get("dim", 0) or 0)
    if dim <= 0:
        raise RuntimeError("ColPali /info did not provide a valid 'dim' for MUVERA")

    logger.info("Initializing MUVERA postprocessor with input_dim=%s", dim)
    return MuveraPostprocessor(input_dim=dim)


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

    muvera_post = None
    if config.MUVERA_ENABLED:
        try:
            muvera_post = _get_muvera_postprocessor_cached()
        except Exception as exc:  # pragma: no cover - defensive guard
            logger.exception(
                "Failed to initialize MUVERA; continuing without it: %s", exc
            )
            _get_muvera_postprocessor_cached.cache_clear()
            muvera_post = None

    return QdrantService(
        api_client=get_colpali_client(),
        minio_service=minio_service,
        muvera_post=muvera_post,
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
    global qdrant_init_error, minio_init_error
    logger.info("Invalidating cached services to apply new configuration")
    qdrant_init_error = None
    minio_init_error = None
    _get_qdrant_service_cached.cache_clear()
    _get_muvera_postprocessor_cached.cache_clear()
    _get_minio_service_cached.cache_clear()
    _get_colpali_client_cached.cache_clear()
