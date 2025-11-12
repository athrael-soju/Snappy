from __future__ import annotations

import asyncio

from api.dependencies import (
    get_duckdb_service,
    get_minio_service,
    get_qdrant_service,
    minio_init_error,
    qdrant_init_error,
)
from fastapi import APIRouter, HTTPException

from .helpers import clear_all_sync, delete_sync, initialize_sync, summarize_status

router = APIRouter(prefix="", tags=["maintenance"])


@router.post("/clear/qdrant")
async def clear_qdrant():
    try:
        svc = get_qdrant_service()
        if not svc:
            raise HTTPException(
                status_code=503,
                detail=f"Service unavailable: {qdrant_init_error or 'Dependency services are down'}",
            )
        msg = await asyncio.to_thread(svc.clear_collection)
        return {"status": "ok", "message": msg}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/clear/minio")
async def clear_minio():
    try:
        msvc = get_minio_service()
        if not msvc:
            raise HTTPException(
                status_code=503,
                detail=f"Service unavailable: {minio_init_error or 'Dependency services are down'}",
            )
        res = await asyncio.to_thread(msvc.clear_images)
        return {
            "status": "ok",
            "deleted": res.get("deleted"),
            "failed": res.get("failed"),
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/clear/all")
async def clear_all():
    try:
        svc = get_qdrant_service()
        msvc = get_minio_service()
        dsvc = get_duckdb_service()
        results = await asyncio.to_thread(clear_all_sync, svc, msvc, dsvc)
        return {"status": summarize_status(results), "results": results}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/initialize")
async def initialize():
    try:
        svc = get_qdrant_service()
        msvc = get_minio_service()
        dsvc = get_duckdb_service()
        return await asyncio.to_thread(initialize_sync, svc, msvc, dsvc)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.delete("/delete")
async def delete_collection_and_bucket():
    try:
        svc = get_qdrant_service()
        msvc = get_minio_service()
        dsvc = get_duckdb_service()
        return await asyncio.to_thread(delete_sync, svc, msvc, dsvc)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
