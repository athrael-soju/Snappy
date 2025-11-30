"""Document search and retrieval."""

import asyncio
import logging
import time
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
    Search for documents using Qdrant.

    Returns search results with inline image data (base64) for display.
    OCR text is included in payload when available and requested.
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

        for it in items:
            payload = it.get("payload", {})
            label = it["label"]

            # Extract inline image data from payload
            image_data = payload.get("image_data")
            image_mime_type = payload.get("image_mime_type")

            # Extract OCR data from payload (inline storage)
            ocr_text = None
            ocr_markdown = None
            if include_ocr:
                ocr_text = payload.get("ocr_text")
                ocr_markdown = payload.get("ocr_markdown")

            results.append(
                SearchItem(
                    image_data=image_data,
                    image_mime_type=image_mime_type,
                    image_url=None,  # No longer using URL-based storage
                    label=label,
                    payload=payload,
                    score=it.get("score"),
                    ocr_text=ocr_text,
                    ocr_markdown=ocr_markdown,
                    json_url=None,  # No longer using URL-based storage
                )
            )

        logger.info(
            "Search completed successfully",
            extra={
                "operation": "search",
                "query": q,
                "result_count": len(results),
                "include_ocr": include_ocr,
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
