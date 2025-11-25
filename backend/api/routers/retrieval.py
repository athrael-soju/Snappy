import asyncio
import logging
from typing import List, Optional

import config  # Import module for dynamic config access
from api.models import SearchItem
from domain.errors import SearchError, ServiceUnavailableError
from domain.retrieval import search_documents
from fastapi import APIRouter, HTTPException, Query

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["retrieval"])


@router.get("/search", response_model=List[SearchItem])
async def search(
    q: str = Query(..., description="User query"),
    k: Optional[int] = Query(None, ge=1, le=50),
    include_ocr: bool = Query(False, description="Include OCR results if available"),
    include_interpretability: Optional[bool] = Query(
        None,
        description="Use ColPali attention maps to filter OCR regions. "
        "When enabled, only regions relevant to the query are returned. "
        "If not specified, uses COLPALI_INTERPRETABILITY_ENABLED config.",
    ),
):
    # Use config default if not provided
    top_k: int = int(k) if k is not None else int(getattr(config, "DEFAULT_TOP_K", 10))

    # Use config default for interpretability if not explicitly provided
    use_interpretability: bool = (
        include_interpretability
        if include_interpretability is not None
        else bool(getattr(config, "COLPALI_INTERPRETABILITY_ENABLED", False))
    )

    logger.info(
        "Search request received",
        extra={
            "operation": "search",
            "query": q,
            "top_k": top_k,
            "include_ocr": include_ocr,
            "include_interpretability": use_interpretability,
        },
    )

    try:
        return await search_documents(q, top_k, include_ocr, use_interpretability)
    except ServiceUnavailableError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except SearchError as e:
        raise HTTPException(status_code=500, detail=str(e))
