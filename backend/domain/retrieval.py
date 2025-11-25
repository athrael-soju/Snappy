import asyncio
import logging
from typing import Any, Dict, List, Optional

import numpy as np

import config
from api.dependencies import get_duckdb_service, get_qdrant_service, qdrant_init_error
from api.models import SearchItem
from domain.errors import SearchError, ServiceUnavailableError
from utils.interpretability import compute_interpretability, filter_regions_by_attention

logger = logging.getLogger(__name__)

# Default patch size for ColPali models
COLPALI_PATCH_SIZE = 32


async def search_documents(
    q: str,
    top_k: int,
    include_ocr: bool,
    include_interpretability: bool = False,
) -> List[SearchItem]:
    """
    Search for documents using Qdrant and optionally enrich with OCR data from DuckDB.

    Args:
        q: Search query string
        top_k: Number of results to return
        include_ocr: Whether to include OCR data from DuckDB
        include_interpretability: Whether to use ColPali attention maps to filter
            OCR regions. When enabled, only regions that intersect with high-attention
            areas are returned. Requires include_ocr=True and grounding enabled.
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
        raise ServiceUnavailableError(f"Service unavailable: {error_msg}")

    try:
        # Use simple timing to avoid blocking event loop with PerformanceTimer
        import time

        # Determine if we need embeddings for interpretability
        include_grounding = getattr(config, "DEEPSEEK_OCR_INCLUDE_GROUNDING", True)
        use_interpretability = (
            include_interpretability
            and include_ocr
            and include_grounding
        )

        start_time = time.perf_counter()
        search_result = await asyncio.to_thread(
            svc.search_with_metadata, q, top_k, None, use_interpretability
        )

        # Extract items and query embedding based on return type
        if use_interpretability and isinstance(search_result, dict):
            items = search_result.get("items", [])
            query_embedding = np.array(search_result.get("query_embedding", []))
        else:
            items = search_result if isinstance(search_result, list) else []
            query_embedding = None

        duration_ms = (time.perf_counter() - start_time) * 1000

        logger.info(
            "Qdrant search completed",
            extra={
                "operation": "search",
                "result_count": len(items),
                "duration_ms": duration_ms,
                "include_vectors": use_interpretability,
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
                    "use_interpretability": use_interpretability,
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
                        grounding_enabled = getattr(config, "DEEPSEEK_OCR_INCLUDE_GROUNDING", True)

                        if grounding_enabled:
                            # Grounding enabled: fetch regions from DuckDB (optimized query)
                            regions = await asyncio.to_thread(
                                duckdb_service.get_page_regions, filename, page_number
                            )

                            if regions:
                                # Apply interpretability filtering if enabled
                                if use_interpretability and query_embedding is not None:
                                    image_embedding = it.get("embedding")
                                    if image_embedding is not None:
                                        # Get image dimensions from payload
                                        image_width = payload.get("page_width_px", 1024)
                                        image_height = payload.get("page_height_px", 1024)

                                        # Compute interpretability maps
                                        interp_result = compute_interpretability(
                                            query_embedding=query_embedding,
                                            image_embedding=np.array(image_embedding),
                                            image_width=image_width,
                                            image_height=image_height,
                                            patch_size=COLPALI_PATCH_SIZE,
                                        )

                                        attention_bboxes = interp_result.get("high_attention_bboxes", [])

                                        if attention_bboxes:
                                            # Filter regions by attention
                                            original_count = len(regions)
                                            regions = filter_regions_by_attention(
                                                regions,
                                                attention_bboxes,
                                                min_overlap_ratio=0.1,
                                            )
                                            logger.debug(
                                                "Interpretability filtering applied",
                                                extra={
                                                    "operation": "search",
                                                    "document_filename": filename,
                                                    "page_number": page_number,
                                                    "original_regions": original_count,
                                                    "filtered_regions": len(regions),
                                                    "attention_areas": len(attention_bboxes),
                                                },
                                            )

                                # Include regions data (image URLs are in image_url field)
                                payload["ocr"] = {
                                    "regions": regions,
                                }
                                ocr_success_count += 1
                            else:
                                # regions is None or empty - log warning
                                logger.warning(
                                    "OCR regions not found in DuckDB",
                                    extra={
                                        "operation": "search",
                                        "document_filename": filename,
                                        "page_number": page_number,
                                    },
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
                                    markdown_content = page_data.get("markdown", "")
                                    if markdown_content:
                                        payload["ocr"] = {
                                            "markdown": markdown_content,
                                        }
                                        ocr_success_count += 1
                                else:  # plain_ocr, describe, custom, locate
                                    text_content = page_data.get("text", "")
                                    if text_content:
                                        payload["ocr"] = {
                                            "text": text_content,
                                        }
                                        ocr_success_count += 1

                                if not payload.get("ocr"):
                                    logger.warning(
                                        "OCR data exists but is empty",
                                        extra={
                                            "operation": "search",
                                            "document_filename": filename,
                                            "page_number": page_number,
                                            "task_type": task_type,
                                        },
                                    )
                            else:
                                logger.warning(
                                    "OCR page data not found in DuckDB",
                                    extra={
                                        "operation": "search",
                                        "document_filename": filename,
                                        "page_number": page_number,
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

    except (ServiceUnavailableError, SearchError):
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
        raise SearchError(str(exc))
