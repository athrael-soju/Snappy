from typing import Optional

from services.colpali import ColPaliService
from services.qdrant import QdrantService, MuveraPostprocessor
from services.minio import MinioService
import config
import logging
logger = logging.getLogger(__name__)

# Singleton-style dependencies with lazy initialization and error capture
api_client = ColPaliService()
muvera_post: Optional[MuveraPostprocessor] = None

qdrant_service: Optional[QdrantService] = None
qdrant_init_error: Optional[str] = None

minio_service: Optional[MinioService] = None
minio_init_error: Optional[str] = None


def get_minio_service() -> Optional[MinioService]:
    global minio_service, minio_init_error
    if minio_service is None:
        try:
            minio_service = MinioService()
            minio_init_error = None
        except Exception as e:
            minio_service = None
            minio_init_error = str(e)
    return minio_service


def get_qdrant_service() -> Optional[QdrantService]:
    global qdrant_service, qdrant_init_error, muvera_post
    
    # Check if service exists but has stale MUVERA configuration
    if qdrant_service is not None:
        service_has_muvera = qdrant_service.muvera_post is not None
        config_wants_muvera = config.MUVERA_ENABLED
        
        if service_has_muvera != config_wants_muvera:
            logger.info("MUVERA config changed (was=%s, now=%s), recreating service", service_has_muvera, config_wants_muvera)
            qdrant_service = None
            muvera_post = None
    
    if qdrant_service is None:
        try:
            # Initialize MUVERA if enabled and input dim is available
            if config.MUVERA_ENABLED:
                if muvera_post is None:
                    try:
                        info = api_client.get_info() or {}
                        dim = int(info.get("dim", 0))
                        if dim > 0:
                            logger.info("Initializing MUVERA with input_dim=%s", dim)
                            muvera_post = MuveraPostprocessor(input_dim=dim)
                        else:
                            logger.warning("MUVERA enabled but ColPali /info returned invalid dim: %s", dim)
                    except Exception:
                        logger.exception("Failed to initialize MUVERA from ColPali /info; continuing without MUVERA")
                        muvera_post = None
            else:
                muvera_post = None  # Clear MUVERA if disabled

            qdrant_service = QdrantService(
                api_client=api_client,
                minio_service=get_minio_service(),
                muvera_post=muvera_post,
            )
            logger.info("QdrantService initialized (muvera_enabled=%s, muvera_dim=%s)", bool(muvera_post), getattr(muvera_post, 'embedding_size', None) if muvera_post else None)
            qdrant_init_error = None
        except Exception as e:
            qdrant_service = None
            qdrant_init_error = str(e)
    return qdrant_service


def invalidate_services():
    """Invalidate service singletons to force re-initialization with new config."""
    global qdrant_service, muvera_post, minio_service
    logger.info("Invalidating service singletons to apply new configuration")
    qdrant_service = None
    muvera_post = None
    # Note: minio_service can be kept as it doesn't change based on runtime config typically
