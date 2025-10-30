"""
OCR API router with endpoints for document processing.
"""

import time
from pathlib import Path

from config.logging_config import get_logger
from config.settings import settings
from fastapi import APIRouter, File, HTTPException, UploadFile, status
from models.api_models import ErrorResponse, OCRElement, OCRResponse
from services.paddleocr_vl_service import paddleocr_vl_service

logger = get_logger(__name__)

router = APIRouter(prefix="/ocr", tags=["OCR"])


@router.post(
    "/extract-document",
    response_model=OCRResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Bad request - invalid file"},
        413: {"model": ErrorResponse, "description": "File too large"},
        500: {"model": ErrorResponse, "description": "Processing error"},
    },
    summary="Extract document structure and text",
    description="Upload an image or PDF file to extract document structure including text, tables, charts, and formulas.",
)
async def extract_document(
    file: UploadFile = File(..., description="Image or PDF file to process")
) -> OCRResponse:
    """
    Extract document structure and text from uploaded file.

    Supports:
    - Image formats: JPEG, PNG, BMP, TIFF
    - PDF documents
    - Multilingual text (109 languages)
    - Tables, charts, formulas

    Returns:
    - Structured JSON with all extracted elements
    - Markdown formatted output
    - Processing metadata
    """
    start_time = time.time()

    try:
        # Validate file extension
        file_ext = Path(file.filename).suffix.lower() if file.filename else ""
        if file_ext not in settings.allowed_extensions:
            logger.warning(f"Invalid file extension: {file_ext}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file format '{file_ext}'. Allowed: {', '.join(settings.allowed_extensions)}",
            )

        # Read file content
        file_content = await file.read()
        file_size = len(file_content)

        # Validate file size
        if file_size > settings.max_upload_size:
            logger.warning(
                f"File too large: {file_size} bytes (max: {settings.max_upload_size})"
            )
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum size: {settings.max_upload_size / (1024*1024):.1f}MB",
            )

        if file_size == 0:
            logger.warning("Empty file uploaded")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Empty file uploaded"
            )

        logger.info(f"Processing file: {file.filename} ({file_size} bytes)")

        # Process image
        results = paddleocr_vl_service.process_image_bytes(
            image_bytes=file_content, filename=file.filename
        )

        # Convert results to response model
        elements = [
            OCRElement(
                index=result["index"],
                content=result["content"],
                metadata=result["metadata"],
            )
            for result in results
        ]

        # Generate markdown output
        markdown = paddleocr_vl_service.get_markdown_output(results)

        processing_time = time.time() - start_time

        logger.info(
            f"Document processed successfully - "
            f"Elements: {len(elements)}, "
            f"Time: {processing_time:.2f}s"
        )

        return OCRResponse(
            success=True,
            message=f"Document processed successfully. Found {len(elements)} elements.",
            processing_time=processing_time,
            elements=elements,
            markdown=markdown,
        )

    except HTTPException:
        raise
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"Error processing document: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Processing error: {str(e)}",
        )
