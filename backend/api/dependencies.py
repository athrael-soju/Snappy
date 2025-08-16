from typing import Optional

from clients.colpali import ColPaliClient
from clients.qdrant import QdrantService
from clients.minio import MinioService

# Singleton-style dependencies with lazy initialization and error capture
api_client = ColPaliClient()

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
            qdrant_service = QdrantService(
                api_client=api_client, minio_service=get_minio_service()
            )
            qdrant_init_error = None
        except Exception as e:
            qdrant_service = None
            qdrant_init_error = str(e)
    return qdrant_service
