from __future__ import annotations

import logging
from typing import List, Optional

from api.progress import progress_manager
from qdrant_client import models
from services.ocr import OcrService
from services.qdrant import QdrantService

logger = logging.getLogger(__name__)


async def get_document_pages(
    qdrant_service: QdrantService,
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


def process_document_background(
    job_id: str,
    ocr_service: OcrService,
    filename: str,
    page_numbers: List[int],
    mode: Optional[str],
    task: Optional[str],
) -> None:
    """Background task for processing entire document."""
    try:
        total = len(page_numbers)
        logger.info("Starting OCR job %s for %s: %s pages", job_id, filename, total)

        for idx, page_num in enumerate(page_numbers, 1):
            if progress_manager.is_cancelled(job_id):
                logger.info("OCR job %s cancelled by user", job_id)
                break

            try:
                logger.info(
                    "OCR job %s: Processing page %s (%s/%s)",
                    job_id,
                    page_num,
                    idx,
                    total,
                )
                result = ocr_service.process_document_page(
                    filename=filename,
                    page_number=page_num,
                    mode=mode,
                    task=task,
                )

                progress_manager.update(
                    job_id,
                    current=idx,
                    message=f"Processing page {page_num} ({idx}/{total})",
                )

                logger.info(
                    "OCR processed page %s/%s for %s: %s",
                    page_num,
                    total,
                    filename,
                    result.get("storage_url"),
                )
            except Exception as page_error:  # noqa: BLE001 - continue job
                logger.exception(
                    "Failed to process page %s for %s: %s",
                    page_num,
                    filename,
                    page_error,
                )
                progress_manager.update(
                    job_id,
                    current=idx,
                    message=f"Failed page {page_num}, continuing ({idx}/{total})",
                )

        if not progress_manager.is_cancelled(job_id):
            progress_manager.complete(
                job_id, message=f"Completed OCR processing for {filename}"
            )
            logger.info("OCR job %s completed successfully", job_id)

    except Exception as exc:  # noqa: BLE001 - ensure failure recorded
        logger.exception("OCR background processing failed: %s", exc)
        progress_manager.fail(job_id, str(exc))


__all__ = ["get_document_pages", "process_document_background"]
