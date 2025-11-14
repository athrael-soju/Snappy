from __future__ import annotations

import logging
from typing import List, Optional

from api.progress import progress_manager
from qdrant_client import models
from clients.ocr import OcrService
from clients.qdrant import QdrantService

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
    """Background task for processing entire document with parallel batch processing."""
    try:
        total = len(page_numbers)
        logger.info("Starting OCR job %s for %s: %s pages", job_id, filename, total)

        # Get max workers from config
        import config

        max_workers = getattr(config, "DEEPSEEK_OCR_MAX_WORKERS", 4)
        max_workers = max(1, int(max_workers))

        # Process pages in batches for better progress tracking and cancellation support
        # Batch size = max_workers to optimize parallel processing
        batch_size = max_workers
        processed_count = 0
        failed_pages = []

        for batch_start in range(0, total, batch_size):
            if progress_manager.is_cancelled(job_id):
                logger.info("OCR job %s cancelled by user", job_id)
                break

            batch_end = min(batch_start + batch_size, total)
            batch_pages = page_numbers[batch_start:batch_end]
            batch_num = (batch_start // batch_size) + 1
            total_batches = (total + batch_size - 1) // batch_size

            logger.info(
                "OCR job %s: Processing batch %s/%s (%s pages in parallel)",
                job_id,
                batch_num,
                total_batches,
                len(batch_pages),
            )

            # Update progress before batch starts
            progress_manager.update(
                job_id,
                current=processed_count,
                message=f"Processing batch {batch_num}/{total_batches} ({processed_count}/{total} pages completed)",
            )

            try:
                # Process batch in parallel
                results = ocr_service.process_document_batch(
                    filename=filename,
                    page_numbers=batch_pages,
                    mode=mode,
                    task=task,
                    max_workers=max_workers,
                )

                # Log results for each page in batch
                for idx, (page_num, result) in enumerate(zip(batch_pages, results)):
                    if result and result.get("status") == "success":
                        logger.info(
                            "OCR processed page %s for %s: %s",
                            page_num,
                            filename,
                            result.get("storage_url"),
                        )
                    elif result and result.get("status") == "error":
                        failed_pages.append(page_num)
                        logger.warning(
                            "Failed to process page %s for %s: %s",
                            page_num,
                            filename,
                            result.get("error", "Unknown error"),
                        )
                    else:
                        failed_pages.append(page_num)
                        logger.warning(
                            "Failed to process page %s for %s: No result returned",
                            page_num,
                            filename,
                        )

                processed_count += len(batch_pages)

                # Update progress after batch completes
                success_count = processed_count - len(failed_pages)
                progress_manager.update(
                    job_id,
                    current=processed_count,
                    message=f"Batch {batch_num}/{total_batches} complete ({success_count}/{processed_count} successful)",
                )

            except Exception as batch_error:  # noqa: BLE001 - continue job
                logger.exception(
                    "Failed to process batch %s for %s: %s",
                    batch_num,
                    filename,
                    batch_error,
                )
                # Mark all pages in failed batch as failed
                failed_pages.extend(batch_pages)
                processed_count += len(batch_pages)
                progress_manager.update(
                    job_id,
                    current=processed_count,
                    message=f"Batch {batch_num} failed, continuing ({processed_count}/{total})",
                )

        if not progress_manager.is_cancelled(job_id):
            if failed_pages:
                message = (
                    f"Completed OCR processing for {filename} "
                    f"({total - len(failed_pages)}/{total} pages successful, "
                    f"{len(failed_pages)} failed)"
                )
            else:
                message = f"Completed OCR processing for {filename} ({total}/{total} pages successful)"

            progress_manager.complete(job_id, message=message)
            logger.info(
                "OCR job %s completed: %s/%s pages successful",
                job_id,
                total - len(failed_pages),
                total,
            )

    except Exception as exc:  # noqa: BLE001 - ensure failure recorded
        logger.exception("OCR background processing failed: %s", exc)
        progress_manager.fail(job_id, str(exc))


__all__ = ["get_document_pages", "process_document_background"]
