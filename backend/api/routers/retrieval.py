import asyncio
from typing import List, Optional

import config  # Import module for dynamic config access
from api.dependencies import get_duckdb_service, get_qdrant_service, qdrant_init_error
from api.models import SearchItem
from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="", tags=["retrieval"])


@router.get("/search", response_model=List[SearchItem])
async def search(
    q: str = Query(..., description="User query"),
    k: Optional[int] = Query(None, ge=1, le=50),
    include_ocr: bool = Query(False, description="Include OCR results if available"),
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

    # Determine OCR data source based on DuckDB availability
    use_duckdb = include_ocr and getattr(config, "DUCKDB_ENABLED", False)
    duckdb_service = get_duckdb_service() if use_duckdb else None

    for it in items:
        payload = it.get("payload", {})
        label = it["label"]
        image_url = payload.get("image_url")
        json_url = None

        if include_ocr:
            filename = payload.get("filename")
            # Use pdf_page_index from Qdrant payload (matches page_number in DuckDB)
            page_number = payload.get("pdf_page_index")

            if filename and page_number is not None:
                if use_duckdb and duckdb_service:
                    # DuckDB enabled: fetch only regions from DuckDB
                    try:
                        page_data = await asyncio.to_thread(
                            duckdb_service.get_page, filename, page_number
                        )
                        if page_data and page_data.get("regions"):
                            # Only include regions data (image URLs are in content field)
                            payload["ocr"] = {
                                "regions": page_data.get("regions", []),
                            }
                    except Exception:
                        # If DuckDB fetch fails, continue without OCR data
                        pass
                else:
                    # DuckDB disabled: use MinIO json_url
                    json_url = payload.get("ocr_url") or payload.get("storage_url")

        results.append(
            SearchItem(
                image_url=image_url,
                label=label,
                payload=payload,
                score=it.get("score"),
                json_url=json_url,
            )
        )
    return results
