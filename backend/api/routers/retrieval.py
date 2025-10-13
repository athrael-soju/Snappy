import asyncio
from typing import List, Optional

import config  # Import module for dynamic config access
from api.dependencies import get_qdrant_service, qdrant_init_error
from api.models import SearchItem
from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="", tags=["retrieval"])


@router.get("/search", response_model=List[SearchItem])
async def search(
    q: str = Query(..., description="User query"),
    k: Optional[int] = Query(None, ge=1, le=50),
):
    # Use config default if not provided
    top_k: int = int(k) if k is not None else int(getattr(config, "DEFAULT_TOP_K", 10))
    svc = get_qdrant_service()
    if not svc:
        raise HTTPException(
            status_code=503,
            detail=f"Service unavailable: {qdrant_init_error or 'Dependency services are down'}",
        )
    items = await asyncio.to_thread(svc.search_with_metadata, q, top_k)
    results: List[SearchItem] = []
    for it in items:
        payload = it.get("payload", {})
        label = it["label"]
        image_url = payload.get("image_url")
        results.append(
            SearchItem(
                image_url=image_url,
                label=label,
                payload=payload,
                score=it.get("score"),
            )
        )
    return results
