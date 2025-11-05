from __future__ import annotations

import logging
from functools import lru_cache
from typing import Optional

import config
from app.integrations.colpali_client import ColPaliClient
from app.integrations.deepseek_client import DeepSeekOCRClient
from app.integrations.minio_client import MinioClient
from app.integrations.qdrant import MuveraPostprocessor, QdrantService

logger = logging.getLogger(__name__)

qdrant_init_error: Optional[str] = None
minio_init_error: Optional[str] = None
deepseek_init_error: Optional[str] = None


@lru_cache(maxsize=1)
def _get_colpali_client_cached() -> ColPaliClient:
    return ColPaliClient()


def get_colpali_client() -> ColPaliClient:
    """Return the cached ColPali service instance."""
    return _get_colpali_client_cached()


class _ColPaliClientProxy:
    """Proxy to preserve existing attribute-style access to the ColPali client."""

    def __getattr__(self, name: str):
        return getattr(get_colpali_client(), name)


api_client = _ColPaliClientProxy()


@lru_cache(maxsize=1)
def _get_deepseek_client_cached() -> DeepSeekOCRClient:
    return DeepSeekOCRClient()


def get_deepseek_client() -> Optional[DeepSeekOCRClient]:
    """Return the cached DeepSeek OCR service if enabled."""
    global deepseek_init_error
    if not config.DEEPSEEK_OCR_ENABLED:
        deepseek_init_error = None
        return None

    try:
        client = _get_deepseek_client_cached()
        deepseek_init_error = None
        return client
    except Exception as exc:  # pragma: no cover - defensive guard
        logger.error("Failed to initialize DeepSeek OCR service: %s", exc)
        deepseek_init_error = str(exc)
        _get_deepseek_client_cached.cache_clear()
        return None


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
def _get_minio_service_cached() -> MinioClient:
    return MinioClient()


def get_minio_service() -> MinioClient:
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
    deepseek_service = get_deepseek_client()

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
        deepseek_service=deepseek_service,
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
    global qdrant_init_error, minio_init_error, deepseek_init_error
    logger.info("Invalidating cached services to apply new configuration")
    qdrant_init_error = None
    minio_init_error = None
    deepseek_init_error = None
    _get_qdrant_service_cached.cache_clear()
    _get_muvera_postprocessor_cached.cache_clear()
    _get_minio_service_cached.cache_clear()
    _get_colpali_client_cached.cache_clear()
    _get_deepseek_client_cached.cache_clear()
