import asyncio
import logging
from typing import List, Optional

import config
from api.dependencies import get_duckdb_service, get_qdrant_service, qdrant_init_error
from api.models import SearchItem
from fastapi import HTTPException

logger = logging.getLogger(__name__)


async def search_documents(
    q: str,
    top_k: int,
    include_ocr: bool,
) -> List[SearchItem]:
    """
    Search for documents using Qdrant and optionally enrich with OCR data from DuckDB.
    """
    svc = get_qdrant_service()
    if not svc:
        error_msg = qdrant_init_error.get() or "Dependency services are down"
        logger.error(
            "Qdrant service unavailable",
            extra={
                "operation": "search",
                "error": error_msg,
            },
        )
        raise HTTPException(
            status_code=503,
            detail=f"Service unavailable: {error_msg}",
        )

    try:
        # Use simple timing to avoid blocking event loop with PerformanceTimer
        import time

        start_time = time.perf_counter()
        items = await asyncio.to_thread(svc.search_with_metadata, q, top_k)
        duration_ms = (time.perf_counter() - start_time) * 1000

        logger.info(
            "Qdrant search completed",
            extra={
                "operation": "search",
                "result_count": len(items),
                "duration_ms": duration_ms,
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
                        # Check if grounding (regions) is enabled
                        include_grounding = getattr(config, "DEEPSEEK_OCR_INCLUDE_GROUNDING", True)
                        
                        if include_grounding:
                            # Grounding enabled: fetch regions from DuckDB (optimized query)
                            regions = await asyncio.to_thread(
                                duckdb_service.get_page_regions, filename, page_number
                            )
                            
                            if regions:
                                # Include regions data (image URLs are in image_url field)
                                payload["ocr"] = {
                                    "regions": regions,
                                }
                                ocr_success_count += 1
                            else:
                                # regions is None or empty - error
                                logger.error(
                                    "DuckDB failed to fetch OCR regions",
                                    extra={
                                        "operation": "search",
                                        "filename": filename,
                                        "page_number": page_number,
                                    },
                                )
                                raise RuntimeError(
                                    f"Failed to fetch OCR regions from DuckDB for {filename} page {page_number}"
                                )
                        else:
                            # Grounding disabled: fetch full page text/markdown
                            page_data = await asyncio.to_thread(
                                duckdb_service.get_page, filename, page_number
                            )
                            if page_data:
                                # Check task type to determine which field to return
                                task_type = getattr(config, "DEEPSEEK_OCR_TASK", "markdown")
                                
                                # Map task types to output fields:
                                # - "markdown" → markdown field
                                # - "plain_ocr", "describe", "custom" → text field
                                # - "locate" → requires grounding, shouldn't be used when grounding disabled
                                if task_type == "markdown":
                                    content = page_data.get("markdown", "")
                                else:  # plain_ocr, describe, custom, locate
                                    content = page_data.get("text", "")
                                
                                payload["ocr"] = {
                                    "content": content,
                                }
                                ocr_success_count += 1
                            else:
                                logger.error(
                                    "DuckDB failed to fetch OCR page data",
                                    extra={
                                        "operation": "search",
                                        "filename": filename,
                                        "page_number": page_number,
                                    },
                                )
                                raise RuntimeError(
                                    f"Failed to fetch OCR data from DuckDB for {filename} page {page_number}"
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
