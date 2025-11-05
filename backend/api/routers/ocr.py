"""OCR processing endpoints."""

import logging
import uuid
from typing import List, Optional

from api.dependencies import get_ocr_service, get_qdrant_service
from api.progress import progress_manager
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from qdrant_client import models
from services.ocr import OcrService
from services.qdrant import QdrantService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ocr", tags=["ocr"])


# Request/Response Models
class OcrPageRequest(BaseModel):
    """Request to process a single page."""

    filename: str = Field(..., description="Document filename in storage")
    page_number: int = Field(..., ge=0, description="Page number to process")
    mode: Optional[str] = Field(None, description="OCR mode (Gundam, Tiny, etc.)")
    task: Optional[str] = Field(
        None, description="Task type (markdown, plain_ocr, etc.)"
    )
    custom_prompt: Optional[str] = Field(
        None, description="Custom prompt for custom tasks"
    )


class OcrBatchRequest(BaseModel):
    """Request to process multiple pages."""

    filename: str = Field(..., description="Document filename in storage")
    page_numbers: List[int] = Field(..., description="Page numbers to process")
    mode: Optional[str] = None
    task: Optional[str] = None
    max_workers: Optional[int] = Field(None, ge=1, le=16)


class OcrDocumentRequest(BaseModel):
    """Request to OCR all pages of an indexed document."""

    filename: str = Field(..., description="Document filename")
    mode: Optional[str] = None
    task: Optional[str] = None


class OcrResponse(BaseModel):
    """OCR processing result."""

    status: str
    filename: str
    page_number: int
    storage_url: str
    text_preview: str
    regions: int
    extracted_images: int


class OcrBatchResponse(BaseModel):
    """Batch OCR processing result."""

    status: str
    total_pages: int
    successful: int
    failed: int
    results: List[dict]


# Endpoints
@router.post("/process-page", response_model=OcrResponse)
async def process_page(
    request: OcrPageRequest,
    ocr_service: OcrService = Depends(get_ocr_service),
):
    """
    Process a single document page with DeepSeek OCR.

    The page must already be indexed and stored in MinIO.
    """
    if not ocr_service:
        raise HTTPException(
            status_code=503,
            detail="OCR service is not available. Check configuration.",
        )

    try:
        result = ocr_service.process_document_page(
            filename=request.filename,
            page_number=request.page_number,
            mode=request.mode,
            task=request.task,
            custom_prompt=request.custom_prompt,
        )
        return result
    except Exception as e:
        logger.exception("OCR processing failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process-batch", response_model=OcrBatchResponse)
async def process_batch(
    request: OcrBatchRequest,
    ocr_service: OcrService = Depends(get_ocr_service),
):
    """
    Process multiple pages from the same document in parallel.
    """
    if not ocr_service:
        raise HTTPException(
            status_code=503,
            detail="OCR service is not available. Check configuration.",
        )

    try:
        results = ocr_service.process_document_batch(
            filename=request.filename,
            page_numbers=request.page_numbers,
            mode=request.mode,
            task=request.task,
            max_workers=request.max_workers,
        )

        successful = sum(1 for r in results if r and r.get("status") == "success")

        return {
            "status": "completed",
            "total_pages": len(results),
            "successful": successful,
            "failed": len(results) - successful,
            "results": results,
        }
    except Exception as e:
        logger.exception("Batch OCR processing failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process-document")
async def process_document(
    request: OcrDocumentRequest,
    background_tasks: BackgroundTasks,
    ocr_service: OcrService = Depends(get_ocr_service),
    qdrant_service: QdrantService = Depends(get_qdrant_service),
):
    """
    Process all pages of an indexed document with OCR.

    This is a long-running operation that runs in the background.
    Use the returned job_id to track progress via SSE.
    """
    if not ocr_service:
        raise HTTPException(
            status_code=503,
            detail="OCR service is not available. Check configuration.",
        )

    if not qdrant_service:
        raise HTTPException(status_code=503, detail="Qdrant service is not available.")

    # Get page count from Qdrant metadata
    page_numbers = await _get_document_pages(qdrant_service, request.filename)

    if not page_numbers:
        raise HTTPException(
            404, f"No indexed pages found for document: {request.filename}"
        )

    # Create background job
    job_id = str(uuid.uuid4())
    progress_manager.create(job_id, total=len(page_numbers))
    progress_manager.start(job_id)

    # Start background processing
    background_tasks.add_task(
        _process_document_background,
        job_id,
        ocr_service,
        request.filename,
        page_numbers,
        request.mode,
        request.task,
    )

    return {
        "job_id": job_id,
        "total_pages": len(page_numbers),
        "filename": request.filename,
    }


@router.get("/progress/{job_id}")
async def get_progress(job_id: str):
    """Get OCR processing progress for a job."""
    job = progress_manager.get(job_id)
    if not job:
        raise HTTPException(404, f"Job not found: {job_id}")
    return job


@router.get("/progress/stream/{job_id}")
async def stream_progress(job_id: str):
    """Stream OCR processing progress via Server-Sent Events."""
    import asyncio

    async def event_generator():
        """Generate SSE events for progress updates."""
        while True:
            job = progress_manager.get(job_id)
            if not job:
                yield f"data: {{'error': 'Job not found'}}\n\n"
                break

            import json

            yield f"data: {json.dumps(job)}\n\n"

            # Stop streaming if job is finished
            if job["status"] in ("completed", "failed", "cancelled"):
                break

            await asyncio.sleep(0.5)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
    )


@router.post("/cancel/{job_id}")
async def cancel_job(job_id: str):
    """Cancel a running OCR job."""
    cancelled = progress_manager.cancel(job_id)
    if not cancelled:
        raise HTTPException(400, f"Job cannot be cancelled: {job_id}")
    return {"status": "cancelled", "job_id": job_id}


@router.get("/health")
async def health_check(
    ocr_service: OcrService = Depends(get_ocr_service),
):
    """Check OCR service health."""
    if not ocr_service:
        raise HTTPException(503, "OCR service is not available. Check configuration.")

    is_healthy = ocr_service.health_check()

    if not is_healthy:
        raise HTTPException(503, "OCR service unavailable")

    return {"status": "healthy"}


# Helper functions
async def _get_document_pages(
    qdrant_service: QdrantService,
    filename: str,
) -> List[int]:
    """Query Qdrant to get all page numbers for a document."""
    try:
        # Use scroll to get all points for this document
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
            limit=10000,  # Reasonable limit for document pages
            with_payload=True,
            with_vectors=False,
        )

        # Extract page numbers from payload
        page_numbers = set()
        for point in points:
            if point.payload and "pdf_page_index" in point.payload:
                page_numbers.add(int(point.payload["pdf_page_index"]))

        return sorted(list(page_numbers))

    except Exception as e:
        logger.exception(f"Failed to get document pages from Qdrant: {e}")
        return []


def _process_document_background(
    job_id: str,
    ocr_service: OcrService,
    filename: str,
    page_numbers: List[int],
    mode: Optional[str],
    task: Optional[str],
):
    """Background task for processing entire document."""
    try:
        total = len(page_numbers)
        logger.info(f"Starting OCR job {job_id} for {filename}: {total} pages")

        for idx, page_num in enumerate(page_numbers, 1):
            # Check for cancellation
            if progress_manager.is_cancelled(job_id):
                logger.info(f"OCR job {job_id} cancelled by user")
                break

            # Process page
            try:
                logger.info(
                    f"OCR job {job_id}: Processing page {page_num} ({idx}/{total})"
                )
                result = ocr_service.process_document_page(
                    filename=filename,
                    page_number=page_num,
                    mode=mode,
                    task=task,
                )

                # Update progress
                progress_manager.update(
                    job_id,
                    current=idx,
                    message=f"Processing page {page_num} ({idx}/{total})",
                )

                logger.info(
                    f"OCR processed page {page_num}/{total} for {filename}: {result.get('storage_url')}"
                )

            except Exception as page_error:
                logger.exception(
                    f"Failed to process page {page_num} for {filename}: {page_error}"
                )
                # Continue processing other pages
                progress_manager.update(
                    job_id,
                    current=idx,
                    message=f"Failed page {page_num}, continuing ({idx}/{total})",
                )

        # Mark as complete if not cancelled
        if not progress_manager.is_cancelled(job_id):
            progress_manager.complete(
                job_id, message=f"Completed OCR processing for {filename}"
            )
            logger.info(f"OCR job {job_id} completed successfully")

    except Exception as e:
        logger.exception(f"OCR background processing failed: {e}")
        progress_manager.fail(job_id, str(e))
