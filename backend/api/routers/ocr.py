from __future__ import annotations

import logging
from typing import Any, Dict

import config
from api.dependencies import get_paddle_ocr_service, paddle_ocr_init_error
from api.models import OCRExtractionResponse, OCRHealthResponse
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from services.paddleocr import PaddleOCRService, PaddleOCRServiceError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ocr", tags=["ocr"])


def _raise_disabled() -> None:
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="PaddleOCR-VL integration is disabled in configuration.",
    )


@router.get(
    "/health",
    response_model=OCRHealthResponse,
    summary="Check PaddleOCR-VL service health",
)
async def health(
    service: PaddleOCRService = Depends(get_paddle_ocr_service),
) -> OCRHealthResponse:
    """Forward a health probe to the OCR microservice."""
    try:
        payload = service.health()
        return OCRHealthResponse.model_validate(payload)
    except PaddleOCRServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Unexpected error while probing OCR health: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error while probing OCR health.",
        ) from exc


@router.get(
    "/info",
    response_model=Dict[str, Any],
    summary="Fetch PaddleOCR-VL service metadata",
)
async def info(
    service: PaddleOCRService = Depends(get_paddle_ocr_service),
) -> Dict[str, Any]:
    """Return root metadata from the OCR microservice."""
    try:
        return service.service_info()
    except PaddleOCRServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Unexpected error while fetching OCR info: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error while fetching OCR info.",
        ) from exc


@router.post(
    "/extract",
    response_model=OCRExtractionResponse,
    summary="Extract structured OCR data from a document",
    responses={
        413: {"description": "File too large"},
        503: {"description": "Service disabled or unavailable"},
    },
)
async def extract_document(
    file: UploadFile = File(..., description="Image or PDF file to process"),
    service: PaddleOCRService = Depends(get_paddle_ocr_service),
) -> OCRExtractionResponse:
    """Upload a document and return the structured OCR response."""
    if not getattr(config, "PADDLE_OCR_ENABLED", False):
        _raise_disabled()

    if paddle_ocr_init_error:
        logger.error(
            "Paddle OCR service initialization error: %s", paddle_ocr_init_error
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"PaddleOCR service failed to initialize: {paddle_ocr_init_error}",
        )

    if not service.enabled:
        _raise_disabled()

    data = await file.read()
    await file.close()

    try:
        payload = service.extract_document(
            file_bytes=data,
            filename=file.filename,
            content_type=file.content_type,
        )
        return OCRExtractionResponse.model_validate(payload)
    except PaddleOCRServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Unexpected error while invoking Paddle OCR: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error while invoking PaddleOCR.",
        ) from exc
