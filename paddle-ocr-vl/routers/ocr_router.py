"""
OCR API router with endpoints for document processing.
"""

import time
from pathlib import Path

from config.logging_config import get_logger
from config.settings import settings
from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
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
    file: UploadFile = File(..., description="Image or PDF file to process"),
    use_layout_detection: bool | None = Form(
        None, description="Enable layout detection within PaddleOCR-VL"
    ),
    layout_threshold: float | None = Form(
        None, description="Confidence threshold for layout detection boxes"
    ),
    layout_nms: float | None = Form(
        None, description="Non-maximum suppression IoU threshold for layout detection"
    ),
    layout_unclip_ratio: float | None = Form(
        None, description="Polygon expansion ratio for layout detection"
    ),
    layout_merge_bboxes_mode: str | None = Form(
        None, description="Merge mode for overlapping layout boxes"
    ),
    use_doc_orientation_classify: bool | None = Form(
        None, description="Toggle document orientation classification"
    ),
    use_doc_unwarping: bool | None = Form(
        None, description="Toggle document perspective unwarping"
    ),
    use_chart_recognition: bool | None = Form(
        None, description="Enable chart parsing pipeline"
    ),
    format_block_content: str | None = Form(
        None, description="Preferred block content serialization format"
    ),
    min_pixels: int | None = Form(
        None, description="Minimum scaling target for the shortest image side"
    ),
    max_pixels: int | None = Form(
        None, description="Maximum scaling target for the longest image side"
    ),
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
        options = {
            "use_layout_detection": use_layout_detection,
            "layout_threshold": layout_threshold,
            "layout_nms": layout_nms,
            "layout_unclip_ratio": layout_unclip_ratio,
            "layout_merge_bboxes_mode": layout_merge_bboxes_mode,
            "use_doc_orientation_classify": use_doc_orientation_classify,
            "use_doc_unwarping": use_doc_unwarping,
            "use_chart_recognition": use_chart_recognition,
            "format_block_content": format_block_content,
            "min_pixels": min_pixels,
            "max_pixels": max_pixels,
        }
        options = {k: v for k, v in options.items() if v is not None}

        results = paddleocr_vl_service.process_image_bytes(
            image_bytes=file_content, filename=file.filename, options=options
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
