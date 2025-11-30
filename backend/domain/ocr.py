"""OCR domain utilities for document processing.

Note: Re-OCR functionality has been removed as documents now store
images and OCR data inline in Qdrant payloads during initial indexing.
"""

from __future__ import annotations

import logging
from typing import List

from qdrant_client import models
from clients.qdrant import QdrantClient

logger = logging.getLogger(__name__)


async def get_document_pages(
    qdrant_service: QdrantClient,
    filename: str,
) -> List[int]:
    """Query Qdrant to get all page numbers for a document."""
    try:
        collection_name = qdrant_service.collection_manager.collection_name

        scroll_filter = models.Filter(
            must=[
                models.FieldCondition(
                    key="filename",
                    match=models.MatchValue(value=filename),
                )
            ]
        )

        points, _ = qdrant_service.collection_manager.service.scroll(
            collection_name=collection_name,
            scroll_filter=scroll_filter,
            limit=10000,
            with_payload=True,
            with_vectors=False,
        )

        page_numbers = {
            int(point.payload["pdf_page_index"])
            for point in points
            if point.payload and "pdf_page_index" in point.payload
        }

        return sorted(page_numbers)
    except Exception as exc:  # noqa: BLE001 - defensive logging
        logger.exception("Failed to get document pages from Qdrant: %s", exc)
        return []
