import asyncio
import logging
from typing import List, Optional

import config  # Import module for dynamic config access
from api.dependencies import get_duckdb_service, get_qdrant_service, qdrant_init_error
from api.models import SearchItem
from fastapi import APIRouter, HTTPException, Query
from utils.timing import PerformanceTimer

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

    svc = get_qdrant_service()
    if not svc:
        logger.error(
            "Qdrant service unavailable",
            extra={
                "operation": "search",
                "error": qdrant_init_error or "Dependency services are down",
            },
        )
        raise HTTPException(
            status_code=503,
            detail=f"Service unavailable: {qdrant_init_error or 'Dependency services are down'}",
        )

    try:
        with PerformanceTimer(
            "search with metadata", log_on_exit=False
        ) as search_timer:
            items = await asyncio.to_thread(svc.search_with_metadata, q, top_k)

        logger.info(
            "Qdrant search completed",
            extra={
                "operation": "search",
                "result_count": len(items),
                "duration_ms": search_timer.duration_ms,
            },
        )

        results: List[SearchItem] = []

        # Determine OCR data source based on DuckDB availability
        use_duckdb = include_ocr and getattr(config, "DUCKDB_ENABLED", False)
        duckdb_service = get_duckdb_service() if use_duckdb else None

        if include_ocr:
            logger.debug(
                "OCR data requested",
                extra={
                    "operation": "search",
                    "use_duckdb": use_duckdb,
                    "duckdb_available": duckdb_service is not None,
                },
            )

        ocr_fetch_count = 0
        ocr_success_count = 0

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
                    ocr_fetch_count += 1
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
                                ocr_success_count += 1
                        except Exception as exc:
                            logger.warning(
                                "DuckDB OCR fetch failed, continuing without OCR data",
                                extra={
                                    "operation": "search",
                                    "filename": filename,
                                    "page_number": page_number,
                                    "error": str(exc),
                                },
                            )
                    else:
                        # DuckDB disabled: use MinIO json_url
                        json_url = payload.get("ocr_url") or payload.get("storage_url")
                        if json_url:
                            ocr_success_count += 1

            results.append(
                SearchItem(
                    image_url=image_url,
                    label=label,
                    payload=payload,
                    score=it.get("score"),
                    json_url=json_url,
                )
            )

        logger.info(
            "Search completed successfully",
            extra={
                "operation": "search",
                "query": q,
                "result_count": len(results),
                "ocr_requested": include_ocr,
                "ocr_fetch_attempts": ocr_fetch_count,
                "ocr_success_count": ocr_success_count,
            },
        )

        return results

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(
            "Search failed",
            exc_info=exc,
            extra={
                "operation": "search",
                "query": q,
                "top_k": top_k,
                "include_ocr": include_ocr,
            },
        )
        raise HTTPException(status_code=500, detail=str(exc))
