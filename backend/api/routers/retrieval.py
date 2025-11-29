import asyncio
import logging
from typing import List, Optional

import config  # Import module for dynamic config access
from api.models import HeatmapResponse, SearchItem
from domain.errors import SearchError, ServiceUnavailableError
from domain.retrieval import generate_heatmap_for_image, search_documents
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["retrieval"])


class HeatmapRequest(BaseModel):
    """Request body for on-demand heatmap generation."""

    query: str
    image_url: str


@router.get("/search", response_model=List[SearchItem])
async def search(
    q: str = Query(..., description="User query"),
    k: Optional[int] = Query(None, ge=1, le=50),
    include_ocr: bool = Query(False, description="Include OCR results if available"),
):
    # Use config default if not provided
    top_k: int = int(k) if k is not None else int(getattr(config, "DEFAULT_TOP_K", 10))

    logger.info(
        "Search request received",
        extra={
            "operation": "search",
            "query": q,
            "top_k": top_k,
            "include_ocr": include_ocr,
        },
    )

    try:
        return await search_documents(q, top_k, include_ocr)
    except ServiceUnavailableError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except SearchError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search/heatmap", response_model=HeatmapResponse)
async def get_heatmap(request: HeatmapRequest):
    """Generate an attention heatmap for a specific image and query on-demand.

    This endpoint fetches the image from the provided URL, generates an attention
    heatmap using ColPali, and returns the heatmap as a base64 data URL.
    """
    # Check if heatmaps are enabled
    if not getattr(config, "COLPALI_SHOW_HEATMAPS", False):
        raise HTTPException(
            status_code=403, detail="Heatmap generation is disabled in configuration"
        )

    logger.info(
        "Heatmap generation requested",
        extra={
            "operation": "heatmap",
            "query": request.query,
            "image_url": request.image_url[:100],  # Truncate for logging
        },
    )

    try:
        result = await generate_heatmap_for_image(request.query, request.image_url)
        if result is None:
            raise HTTPException(
                status_code=500, detail="Failed to generate heatmap for the image"
            )
        return result
    except ServiceUnavailableError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Heatmap generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
