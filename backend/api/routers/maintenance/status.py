from __future__ import annotations

import asyncio

from api.dependencies import get_storage_service, get_qdrant_service
from fastapi import APIRouter, HTTPException

from domain.maintenance import (
    collect_bucket_status,
    collect_collection_status,
)

router = APIRouter(prefix="", tags=["maintenance"])


@router.get("/status")
async def get_status():
    """Get the status of collection and bucket including statistics."""
    try:
        svc = get_qdrant_service()
        msvc = get_storage_service()
        collection_status, bucket_status = await asyncio.gather(
            asyncio.to_thread(collect_collection_status, svc),
            asyncio.to_thread(collect_bucket_status, msvc),
        )
        return {
            "collection": collection_status,
            "bucket": bucket_status,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
