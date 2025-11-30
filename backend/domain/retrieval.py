import asyncio
import logging
from typing import List

from api.dependencies import get_qdrant_service, qdrant_init_error
from api.models import SearchItem
from domain.errors import SearchError, ServiceUnavailableError

logger = logging.getLogger(__name__)


async def search_documents(
    q: str,
    top_k: int,
    include_ocr: bool,
) -> List[SearchItem]:
    """
    Search for documents using Qdrant with inline image and OCR data.
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

        ocr_success_count = 0

        for it in items:
            payload = it.get("payload", {})
            label = it["label"]

            # Image data is now stored inline as base64
            image_data = payload.get("image_data")
            image_format = payload.get("image_format")
            image_mime_type = payload.get("image_mime_type")

            # Construct data URI for frontend if image data exists
            image_url = None
            if image_data and image_mime_type:
                image_url = f"data:{image_mime_type};base64,{image_data}"

            # OCR data is stored inline in Qdrant payload
            if include_ocr:
                ocr_data = payload.get("ocr_data")
                if ocr_data:
                    # Add OCR data to payload for frontend
                    payload["ocr"] = ocr_data
                    ocr_success_count += 1

            results.append(
                SearchItem(
                    image_url=image_url,
                    label=label,
                    payload=payload,
                    score=it.get("score"),
                    json_url=None,  # No longer used with inline storage
                )
            )

        logger.info(
            "Search completed successfully",
            extra={
                "operation": "search",
                "query": q,
                "result_count": len(results),
                "ocr_requested": include_ocr,
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
