from typing import Optional

from services.colpali import ColPaliService
from services.qdrant import QdrantService, MuveraPostprocessor
from services.minio import MinioService
from config import MUVERA_ENABLED
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
    global qdrant_service, qdrant_init_error
    if qdrant_service is None:
        try:
            # Initialize MUVERA if enabled and input dim is available
            global muvera_post
            if MUVERA_ENABLED and muvera_post is None:
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
