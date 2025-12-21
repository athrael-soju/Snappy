import asyncio

from __version__ import __version__
from api.dependencies import (
    colpali_init_error,
    get_colpali_client,
    get_storage_service,
    get_ocr_service,
    get_qdrant_service,
    ocr_init_error,
    qdrant_init_error,
    storage_init_error,
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
    colpali_ok, storage_ok, qdrant_ok, ocr_ok = await asyncio.gather(
        asyncio.to_thread(_check_colpali),
        asyncio.to_thread(_check_storage),
        asyncio.to_thread(_check_qdrant),
        asyncio.to_thread(_check_ocr),
    )

    # Core services must be healthy; OCR is optional
    core_ok = colpali_ok and storage_ok and qdrant_ok
    response: dict[str, object] = {
        "status": "ok" if core_ok else "degraded",
        "colpali": colpali_ok,
        "storage": storage_ok,
        "qdrant": qdrant_ok,
        "ocr": ocr_ok,
    }

    # Add error messages if present
    colpali_err = colpali_init_error.get()
    if colpali_err:
        response["colpali_init_error"] = colpali_err
    qdrant_err = qdrant_init_error.get()
    if qdrant_err:
        response["qdrant_init_error"] = qdrant_err
    storage_err = storage_init_error.get()
    if storage_err:
        response["storage_init_error"] = storage_err
    ocr_err = ocr_init_error.get()
    if ocr_err:
        response["ocr_init_error"] = ocr_err

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


def _check_storage() -> bool:
    try:
        svc = get_storage_service()
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
