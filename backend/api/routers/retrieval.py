import logging
from typing import List

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
    k: int = Query(default=10, ge=1, le=50, description="Number of results to return"),
    include_ocr: bool = Query(False, description="Include OCR results if available"),
):
    top_k: int = k if k else int(getattr(config, "DEFAULT_TOP_K", 10))

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
