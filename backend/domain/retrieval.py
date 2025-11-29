import asyncio
import io
import logging
from typing import List, Optional

import config
import requests
from api.dependencies import get_duckdb_service, get_qdrant_service, qdrant_init_error
from api.models import HeatmapResponse, SearchItem
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
) -> List[SearchItem]:
    """
    Search for documents using Qdrant and optionally enrich with OCR data from DuckDB.

    Args:
        q: Search query string
        top_k: Number of results to return
        include_ocr: Include OCR data if available
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


async def generate_heatmap_for_image(
    query: str, image_url: str
) -> Optional[HeatmapResponse]:
    """
    Generate an attention heatmap for a single image on-demand.

    Fetches the image from the URL, generates a heatmap via ColPali service,
    and returns the result as a HeatmapResponse.

    Args:
        query: The search query used for similarity computation
        image_url: URL of the image to generate heatmap for

    Returns:
        HeatmapResponse with the heatmap data URL, or None if generation failed
    """
    # Fetch the image
    image = await asyncio.to_thread(_fetch_image_from_url, image_url)
    if image is None:
        logger.warning(f"Failed to fetch image for heatmap: {image_url[:100]}")
        return None

    # Generate heatmap via ColPali service
    colpali_client = ColPaliClient()
    heatmap_results = await asyncio.to_thread(
        colpali_client.generate_heatmaps, query, [image]
    )

    if not heatmap_results or not heatmap_results[0].get("heatmap"):
        logger.warning("ColPali service returned empty heatmap result")
        return None

    heatmap = heatmap_results[0]
    data_url = f"data:image/png;base64,{heatmap['heatmap']}"

    return HeatmapResponse(
        heatmap_url=data_url,
        width=heatmap.get("width", 0),
        height=heatmap.get("height", 0),
    )
