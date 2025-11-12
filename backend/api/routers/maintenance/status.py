from __future__ import annotations

import asyncio

from api.dependencies import get_duckdb_service, get_minio_service, get_qdrant_service
from fastapi import APIRouter, HTTPException

from .helpers import (
    collect_bucket_status,
    collect_collection_status,
    collect_duckdb_status,
)

router = APIRouter(prefix="", tags=["maintenance"])


@router.get("/status")
async def get_status():
    """Get the status of collection and bucket including statistics."""
    try:
        svc = get_qdrant_service()
        msvc = get_minio_service()
        dsvc = get_duckdb_service()
        collection_status, bucket_status = await asyncio.gather(
            asyncio.to_thread(collect_collection_status, svc),
            asyncio.to_thread(collect_bucket_status, msvc),
        )
        duckdb_status = await asyncio.to_thread(collect_duckdb_status, dsvc)
        return {
            "collection": collection_status,
            "bucket": bucket_status,
            "duckdb": duckdb_status,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
