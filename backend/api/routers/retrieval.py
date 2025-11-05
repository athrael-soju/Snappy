import asyncio
from typing import List, Optional

import config  # Import module for dynamic config access
from api.dependencies import get_ocr_service, get_qdrant_service, qdrant_init_error
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

    # Get OCR service if user requested OCR data
    ocr_service = None
    if include_ocr:
        ocr_service = get_ocr_service()

    for it in items:
        payload = it.get("payload", {})
        label = it["label"]
        image_url = payload.get("image_url")
        json_url = payload.get("ocr_url") or payload.get("storage_url")

        # If OCR is requested and available, fetch OCR result from storage
        if include_ocr and ocr_service:
            filename = payload.get("filename")
            page_number = payload.get("page_number")

            if filename and page_number is not None:
                ocr_data = await asyncio.to_thread(
                    ocr_service.fetch_ocr_result, filename, page_number
                )
                if ocr_data:
                    # Add OCR data to payload
                    payload["ocr"] = {
                        "text": ocr_data.get("text", ""),
                        "markdown": ocr_data.get("markdown", ""),
                        "regions": ocr_data.get("regions", []),
                        "extracted_images": ocr_data.get("extracted_images", []),
                    }
                    # Set json_url if available in OCR data
                    json_url = ocr_data.get("storage_url") or json_url

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
