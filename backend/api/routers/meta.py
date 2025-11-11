import asyncio

from __version__ import __version__
from api.dependencies import (
    colpali_init_error,
    duckdb_init_error,
    get_colpali_client,
    get_duckdb_service,
    get_minio_service,
    get_ocr_service,
    get_qdrant_service,
    minio_init_error,
    ocr_init_error,
    qdrant_init_error,
)
from fastapi import APIRouter

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
    colpali_ok, minio_ok, qdrant_ok, duckdb_ok, ocr_ok = await asyncio.gather(
        asyncio.to_thread(_check_colpali),
        asyncio.to_thread(_check_minio),
        asyncio.to_thread(_check_qdrant),
        asyncio.to_thread(_check_duckdb),
        asyncio.to_thread(_check_ocr),
    )

    # Core services must be healthy; OCR is optional
    core_ok = colpali_ok and minio_ok and qdrant_ok and duckdb_ok
    response: dict[str, object] = {
        "status": "ok" if core_ok else "degraded",
        "colpali": colpali_ok,
        "minio": minio_ok,
        "qdrant": qdrant_ok,
        "duckdb": duckdb_ok,
        "ocr": ocr_ok,
    }
    if colpali_init_error:
        response["colpali_init_error"] = colpali_init_error
    if qdrant_init_error:
        response["qdrant_init_error"] = qdrant_init_error
    if minio_init_error:
        response["minio_init_error"] = minio_init_error
    if duckdb_init_error:
        response["duckdb_init_error"] = duckdb_init_error
    if ocr_init_error:
        response["ocr_init_error"] = ocr_init_error
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


def _check_ocr() -> bool:
    try:
        service = get_ocr_service()
        # If service is disabled (None), consider it "healthy" (not an error)
        if service is None:
            return True
        return bool(service.health_check())
    except Exception:
        return False


def _check_duckdb() -> bool:
    try:
        svc = get_duckdb_service()
        if not svc:
            return False
        return svc.health_check()
    except Exception:
        return False
