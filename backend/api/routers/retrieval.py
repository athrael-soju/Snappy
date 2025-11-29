import asyncio
import logging
from typing import List, Optional

import config  # Import module for dynamic config access
import requests
from api.models import SearchItem
from domain.errors import SearchError, ServiceUnavailableError
from domain.retrieval import search_documents
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response
from PIL import Image
from io import BytesIO

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["retrieval"])


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


@router.get("/heatmap", response_class=Response)
async def get_heatmap(
    image_url: str = Query(..., description="URL of the document page image"),
    query: str = Query(..., description="Search query text"),
    alpha: float = Query(0.5, ge=0.0, le=1.0, description="Heatmap transparency"),
):
    """Generate attention heatmap for a query-image pair.

    Fetches the image from the provided URL, generates an attention heatmap
    using the ColPali service, and returns a PNG image with the heatmap overlay.

    The heatmap visualizes which regions of the document are most relevant
    to the search query based on the ColPali model's late interaction attention.

    Args:
        image_url: URL of the document page image (typically from MinIO)
        query: The search query to visualize attention for
        alpha: Heatmap overlay transparency (0=invisible, 1=opaque)

    Returns:
        PNG image with heatmap overlay
    """
    from api.dependencies import get_colpali_client

    logger.info(
        "Heatmap request received",
        extra={
            "operation": "heatmap",
            "query": query[:50] + "..." if len(query) > 50 else query,
            "image_url": image_url[:100] + "..." if len(image_url) > 100 else image_url,
        },
    )

    colpali_client = get_colpali_client()
    if not colpali_client:
        raise HTTPException(
            status_code=503,
            detail="ColPali service is unavailable",
        )

    try:
        # Fetch image from URL
        img_response = await asyncio.to_thread(
            requests.get, image_url, timeout=30
        )
        img_response.raise_for_status()

        # Load image
        image = Image.open(BytesIO(img_response.content)).convert("RGB")

        # Generate heatmap
        heatmap_bytes = await asyncio.to_thread(
            colpali_client.generate_heatmap,
            image,
            query,
            alpha,
        )

        logger.info(
            "Heatmap generated successfully",
            extra={
                "operation": "heatmap",
                "query": query[:50] + "..." if len(query) > 50 else query,
                "size_bytes": len(heatmap_bytes),
            },
        )

        return Response(
            content=heatmap_bytes,
            media_type="image/png",
            headers={
                "Content-Disposition": "inline; filename=heatmap.png",
                "Cache-Control": "public, max-age=3600",  # Cache for 1 hour
            },
        )

    except requests.RequestException as e:
        logger.error(
            "Failed to fetch image for heatmap",
            extra={
                "operation": "heatmap",
                "image_url": image_url,
                "error": str(e),
            },
        )
        raise HTTPException(
            status_code=502,
            detail=f"Failed to fetch image: {str(e)}",
        )
    except Exception as e:
        logger.error(
            "Failed to generate heatmap",
            exc_info=e,
            extra={
                "operation": "heatmap",
                "query": query,
            },
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate heatmap: {str(e)}",
        )
