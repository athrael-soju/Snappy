import asyncio
import logging
from typing import List, Optional

import config
from api.dependencies import (
    get_colpali_client,
    get_duckdb_service,
    get_qdrant_service,
    qdrant_init_error,
)
from api.models import SearchItem
from domain.errors import SearchError, ServiceUnavailableError
from domain.region_relevance import filter_regions_by_relevance

logger = logging.getLogger(__name__)


async def _filter_regions_by_interpretability(
    regions: List,
    query: str,
    image_url: Optional[str],
    payload: dict,
) -> List:
    """
    Filter regions using interpretability maps.

    Args:
        regions: List of OCR regions to filter
        query: Search query text
        image_url: URL of the page image
        payload: Qdrant payload containing image dimensions

    Returns:
        Filtered list of regions with relevance scores

    Raises:
        ServiceUnavailableError: If ColPali client is not available
        SearchError: If any step in the filtering process fails
    """
    # Get configuration
    threshold = float(getattr(config, "REGION_RELEVANCE_THRESHOLD", 0.3))
    top_k = int(getattr(config, "REGION_TOP_K", 0))
    aggregation = getattr(config, "REGION_SCORE_AGGREGATION", "max")

    # Validate top_k (0 means no limit)
    top_k_param = None if top_k == 0 else top_k

    # Get ColPali client
    colpali_client = get_colpali_client()
    if not colpali_client:
        raise ServiceUnavailableError(
            "ColPali client not available - required for region-level retrieval"
        )

    # Get image dimensions from payload
    page_width = payload.get("page_width_px")
    page_height = payload.get("page_height_px")

    if not page_width or not page_height:
        raise SearchError(
            "Page dimensions not found in payload - required for region filtering"
        )

    if not image_url:
        raise SearchError("Image URL not found - required for region filtering")

    # Fetch and load the image
    from io import BytesIO

    import requests
    from PIL import Image

    logger.debug(f"Fetching image from {image_url} for region filtering")
    response = requests.get(image_url, timeout=10)
    response.raise_for_status()
    image = Image.open(BytesIO(response.content))

    # Generate interpretability maps
    logger.debug("Generating interpretability maps for region filtering")
    interp_result = await asyncio.to_thread(
        colpali_client.generate_interpretability_maps,
        query,
        image,
    )

    # Extract interpretability data
    similarity_maps = interp_result.get("similarity_maps", [])
    n_patches_x = interp_result.get("n_patches_x", 0)
    n_patches_y = interp_result.get("n_patches_y", 0)
    image_width = interp_result.get("image_width", page_width)
    image_height = interp_result.get("image_height", page_height)

    if not similarity_maps or not n_patches_x or not n_patches_y:
        raise SearchError(
            f"Invalid interpretability response: similarity_maps={len(similarity_maps) if similarity_maps else 0}, "
            f"n_patches_x={n_patches_x}, n_patches_y={n_patches_y}"
        )

    # Filter regions by relevance
    filtered_regions = filter_regions_by_relevance(
        regions=regions,
        similarity_maps=similarity_maps,
        n_patches_x=n_patches_x,
        n_patches_y=n_patches_y,
        image_width=image_width,
        image_height=image_height,
        threshold=threshold,
        top_k=top_k_param,
        aggregation=aggregation,
    )

    logger.info(
        f"Region filtering applied: {len(regions)} -> {len(filtered_regions)} regions",
        extra={
            "operation": "region_filtering",
            "original_count": len(regions),
            "filtered_count": len(filtered_regions),
            "threshold": threshold,
            "top_k": top_k,
            "aggregation": aggregation,
        },
    )

    return filtered_regions


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
        raise ServiceUnavailableError(f"Service unavailable: {error_msg}")

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
                                # Check if region-level retrieval is enabled
                                enable_region_filtering = getattr(
                                    config, "ENABLE_REGION_LEVEL_RETRIEVAL", False
                                )

                                if enable_region_filtering:
                                    # Apply interpretability-based region filtering
                                    regions = await _filter_regions_by_interpretability(
                                        regions=regions,
                                        query=q,
                                        image_url=image_url,
                                        payload=payload,
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
