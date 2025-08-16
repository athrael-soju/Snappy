from typing import List

from fastapi import APIRouter, HTTPException, Query

from api.dependencies import get_qdrant_service, qdrant_init_error
from api.models import SearchItem
from config import DEFAULT_TOP_K

router = APIRouter(prefix="", tags=["retrieval"])


@router.get("/search", response_model=List[SearchItem])
async def search(
    q: str = Query(..., description="User query"),
    k: int = Query(DEFAULT_TOP_K, ge=1, le=50),
):
    svc = get_qdrant_service()
    if not svc:
        raise HTTPException(
            status_code=503,
            detail=f"Service unavailable: {qdrant_init_error or 'Dependency services are down'}",
        )
    items = svc.search_with_metadata(q, k=k)
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
