from __future__ import annotations

import logging
from typing import List, Optional

from api.progress import progress_manager
from qdrant_client import models
from clients.ocr import OcrClient
from clients.qdrant import QdrantClient
from domain.ocr_persistence import OcrStorageHandler
import config
from typing import Any, Dict

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


def _fetch_page_image(ocr_service: OcrClient, document_id: str, page_number: int) -> bytes:
    """Fetch page image bytes from MinIO."""
    # List objects in the image/ subfolder for this page
    prefix = f"{document_id}/{page_number}/image/"

    for obj in ocr_service.minio_service.service.list_objects(
        bucket_name=ocr_service.minio_service.bucket_name,
        prefix=prefix,
    ):
        object_name = getattr(obj, "object_name", "")
        if object_name:
            # Found the page image, fetch it
            response = ocr_service.minio_service.service.get_object(
                bucket_name=ocr_service.minio_service.bucket_name,
                object_name=object_name,
            )
            return response.read()

    # No image found
    raise FileNotFoundError(
        f"Page image not found for document {document_id} page {page_number} in image/ subfolder"
    )


def process_document_page(
    ocr_service: OcrClient,
    document_id: str,
    filename: str,
    page_number: int,
    *,
    mode: Optional[str] = None,
    task: Optional[str] = None,
    custom_prompt: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Process a single document page with OCR."""
    image_bytes = _fetch_page_image(ocr_service, document_id, page_number)

    ocr_result = ocr_service.processor.process_single(
        image_bytes=image_bytes,
        filename=f"{filename}/page_{page_number}.png",
        mode=mode,
        task=task,
        custom_prompt=custom_prompt,
        include_grounding=ocr_service.default_include_grounding,
        include_images=ocr_service.default_include_images,
    )

    # Ensure filename is in metadata
    if metadata is None:
        metadata = {}
    metadata["filename"] = filename

    # Create storage handler
    storage = OcrStorageHandler(
        minio_service=ocr_service.minio_service,
        processor=ocr_service.processor,
        duckdb_service=getattr(ocr_service, "duckdb_service", None),
    )

    storage_url = storage.store_ocr_result(
        ocr_result=ocr_result,
        document_id=document_id,
        page_number=page_number,
        metadata=metadata,
    )

    return {
        "status": "success",
        "filename": filename,
        "page_number": page_number,
        "storage_url": storage_url,
        "text_preview": ocr_result.get("text", "")[:200],
        "regions": len(ocr_result.get("regions", [])),
        "extracted_images": len(ocr_result.get("crops", [])),
    }


def process_document_batch(
    ocr_service: OcrClient,
    filename: str,
    page_numbers: List[int],
    *,
    mode: Optional[str] = None,
    task: Optional[str] = None,
    max_workers: Optional[int] = None,
) -> List[Optional[Dict[str, Any]]]:
    """Process multiple pages from the same document in parallel."""
    # Create storage handler
    storage = OcrStorageHandler(
        minio_service=ocr_service.minio_service,
        processor=ocr_service.processor,
        duckdb_service=getattr(ocr_service, "duckdb_service", None),
    )

    return ocr_service.processor.process_batch(
        filename=filename,
        page_numbers=page_numbers,
        minio_service=ocr_service.minio_service,
        storage_handler=storage,
        mode=mode,
        task=task,
        max_workers=max_workers,
    )


def process_document_background(
    job_id: str,
    ocr_service: OcrClient,
    filename: str,
    page_numbers: List[int],
    mode: Optional[str],
    task: Optional[str],
) -> None:
    """Background task for processing entire document with parallel batch processing."""
    try:
        total = len(page_numbers)
        logger.info("Starting OCR job %s for %s: %s pages", job_id, filename, total)

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
                # Process batch in parallel using local domain function
                results = process_document_batch(
                    ocr_service=ocr_service,
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
