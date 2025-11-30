from __future__ import annotations

import asyncio

from api.dependencies import get_qdrant_service
from fastapi import APIRouter, HTTPException

from domain.maintenance import collect_collection_status

router = APIRouter(prefix="", tags=["maintenance"])


@router.get("/status")
async def get_status():
    """Get the status of Qdrant collection including statistics."""
    try:
        svc = get_qdrant_service()
        collection_status = await asyncio.to_thread(collect_collection_status, svc)
        return {
            "collection": collection_status,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
