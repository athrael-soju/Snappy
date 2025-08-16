from fastapi import APIRouter

from api.dependencies import (
    api_client,
    get_minio_service,
    get_qdrant_service,
    qdrant_init_error,
    minio_init_error,
)

router = APIRouter(tags=["meta"])


@router.get("/")
async def root():
    return {
        "name": "Vision RAG API",
        "endpoints": [
            "/health",
            "/search",
            "/chat",
            "/chat/stream",
            "/index",
            "/clear/*",
        ],
    }


@router.get("/health")
async def health():
    colpali_ok = False
    minio_ok = False
    qdrant_ok = False
    try:
        colpali_ok = bool(api_client.health_check())
    except Exception:
        colpali_ok = False
    try:
        msvc = get_minio_service()
        minio_ok = bool(msvc and msvc.health_check())
    except Exception:
        minio_ok = False
    try:
        qsvc = get_qdrant_service()
        qdrant_ok = bool(qsvc and qsvc.health_check())
    except Exception:
        qdrant_ok = False

    response: dict[str, object] = {
        "status": "ok" if (colpali_ok and minio_ok and qdrant_ok) else "degraded",
        "colpali": colpali_ok,
        "minio": minio_ok,
        "qdrant": qdrant_ok,
    }
    if qdrant_init_error:
        response["qdrant_init_error"] = qdrant_init_error
    if minio_init_error:
        response["minio_init_error"] = minio_init_error
    return response
