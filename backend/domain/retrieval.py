import asyncio
import io
import logging
from typing import List, Optional

import config
import requests
from api.dependencies import get_duckdb_service, get_qdrant_service, qdrant_init_error
from api.models import SearchItem
from clients.colpali import ColPaliClient
from domain.errors import SearchError, ServiceUnavailableError
from PIL import Image

logger = logging.getLogger(__name__)


def _fetch_image_from_url(url: str) -> Optional[Image.Image]:
    """Fetch an image from a URL and return as PIL Image."""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return Image.open(io.BytesIO(response.content))
    except Exception as e:
        logger.warning(f"Failed to fetch image from {url}: {e}")
        return None


async def search_documents(
    q: str,
    top_k: int,
    include_ocr: bool,
    show_heatmaps: Optional[bool] = None,
) -> List[SearchItem]:
    """
    Search for documents using Qdrant and optionally enrich with OCR data from DuckDB.

    Args:
        q: Search query string
        top_k: Number of results to return
        include_ocr: Include OCR data if available
        show_heatmaps: Generate attention heatmaps (defaults to config setting)
    """
    # Determine if heatmaps should be generated
    if show_heatmaps is None:
        show_heatmaps = getattr(config, "COLPALI_SHOW_HEATMAPS", False)
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

        # Generate heatmaps if enabled
        heatmap_count = 0
        if show_heatmaps and results:
            try:
                heatmap_count = await _generate_heatmaps_for_results(q, results)
            except Exception as e:
                logger.warning(
                    "Heatmap generation failed, returning results without heatmaps",
                    extra={
                        "operation": "search",
                        "error": str(e),
                    },
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
                "heatmaps_generated": heatmap_count,
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


async def _generate_heatmaps_for_results(
    query: str, results: List[SearchItem]
) -> int:
    """
    Generate attention heatmaps for search results.

    Fetches images from their URLs, generates heatmaps via ColPali service,
    and updates each SearchItem's heatmap_url field with a data URL.

    Args:
        query: The search query used for similarity computation
        results: List of SearchItem objects to enrich with heatmaps

    Returns:
        Number of heatmaps successfully generated
    """
    # Collect image URLs and indices
    image_urls = []
    indices = []
    for i, result in enumerate(results):
        if result.image_url:
            image_urls.append(result.image_url)
            indices.append(i)

    if not image_urls:
        return 0

    # Fetch images in parallel
    images: List[Optional[Image.Image]] = await asyncio.to_thread(
        lambda: [_fetch_image_from_url(url) for url in image_urls]
    )

    # Filter out failed fetches
    valid_images = []
    valid_indices = []
    for img, idx in zip(images, indices):
        if img is not None:
            valid_images.append(img)
            valid_indices.append(idx)

    if not valid_images:
        logger.warning("No images could be fetched for heatmap generation")
        return 0

    # Generate heatmaps via ColPali service
    colpali_client = ColPaliClient()
    heatmap_results = await asyncio.to_thread(
        colpali_client.generate_heatmaps, query, valid_images
    )

    # Update results with heatmap data URLs
    success_count = 0
    for heatmap, idx in zip(heatmap_results, valid_indices):
        if heatmap and heatmap.get("heatmap"):
            # Create data URL from base64 encoded PNG
            data_url = f"data:image/png;base64,{heatmap['heatmap']}"
            results[idx].heatmap_url = data_url
            success_count += 1

    return success_count
