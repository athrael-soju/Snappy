import asyncio

from api.dependencies import (
    get_colpali_client,
    get_minio_service,
    get_qdrant_service,
    minio_init_error,
    qdrant_init_error,
)
from fastapi import APIRouter

from backend.__version__ import __version__

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
    colpali_ok, minio_ok, qdrant_ok = await asyncio.gather(
        asyncio.to_thread(_check_colpali),
        asyncio.to_thread(_check_minio),
        asyncio.to_thread(_check_qdrant),
    )

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


@router.get("/version")
async def version():
    """Get the current version of the backend API."""
    return {
        "version": __version__,
        "name": "Snappy Backend",
    }


def _check_colpali() -> bool:
    try:
        client = get_colpali_client()
        return bool(client and client.health_check())
    except Exception:
        return False


def _check_minio() -> bool:
    try:
        svc = get_minio_service()
        return bool(svc and svc.health_check())
    except Exception:
        return False


def _check_qdrant() -> bool:
    try:
        svc = get_qdrant_service()
        return bool(svc and svc.health_check())
    except Exception:
        return False
