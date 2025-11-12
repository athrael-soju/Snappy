from __future__ import annotations

import logging
import uuid

from api.dependencies import get_ocr_service, get_qdrant_service
from api.progress import progress_manager
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from services.ocr import OcrService
from services.qdrant import QdrantService

from .models import (
    OcrBatchRequest,
    OcrBatchResponse,
    OcrDocumentRequest,
    OcrPageRequest,
    OcrResponse,
)
from .tasks import get_document_pages, process_document_background

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["ocr"])


@router.post("/process-page", response_model=OcrResponse)
async def process_page(
    request: OcrPageRequest,
    ocr_service: OcrService = Depends(get_ocr_service),
):
    """Process a single document page with DeepSeek OCR."""
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
    except Exception as exc:
        logger.exception("OCR processing failed")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/process-batch", response_model=OcrBatchResponse)
async def process_batch(
    request: OcrBatchRequest,
    ocr_service: OcrService = Depends(get_ocr_service),
):
    """Process multiple pages from the same document in parallel."""
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
    except Exception as exc:
        logger.exception("Batch OCR processing failed")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/process-document")
async def process_document(
    request: OcrDocumentRequest,
    background_tasks: BackgroundTasks,
    ocr_service: OcrService = Depends(get_ocr_service),
    qdrant_service: QdrantService = Depends(get_qdrant_service),
):
    """Process all pages of an indexed document with OCR."""
    if not ocr_service:
        raise HTTPException(
            status_code=503,
            detail="OCR service is not available. Check configuration.",
        )

    if not qdrant_service:
        raise HTTPException(status_code=503, detail="Qdrant service is not available.")

    page_numbers = await get_document_pages(qdrant_service, request.filename)

    if not page_numbers:
        raise HTTPException(
            404, f"No indexed pages found for document: {request.filename}"
        )

    job_id = str(uuid.uuid4())
    progress_manager.create(job_id, total=len(page_numbers))
    progress_manager.start(job_id)

    background_tasks.add_task(
        process_document_background,
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


__all__ = [
    "health_check",
    "process_batch",
    "process_document",
    "process_page",
]
