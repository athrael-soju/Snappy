"""OCR router for service health checks.

Note: Re-OCR functionality has been removed as documents now store
images and OCR data inline in Qdrant payloads during initial indexing.
To re-process OCR, documents should be re-indexed.
"""

from __future__ import annotations

import logging

from api.dependencies import get_ocr_service
from fastapi import APIRouter, Depends, HTTPException
from clients.ocr import OcrClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["ocr"])


@router.get("/health")
async def health_check(
    ocr_service: OcrClient = Depends(get_ocr_service),
):
    """Check OCR service health."""
    if not ocr_service:
        logger.error(
            "OCR health check failed: service not configured",
            extra={"operation": "health_check", "error": "service_unavailable"},
        )
        raise HTTPException(503, "OCR service is not available. Check configuration.")

    is_healthy = ocr_service.health_check()

    if not is_healthy:
        logger.warning(
            "OCR health check failed: service unhealthy",
            extra={"operation": "health_check", "is_healthy": False},
        )
        raise HTTPException(503, "OCR service unavailable")

    logger.debug("OCR health check passed", extra={"operation": "health_check"})

    return {"status": "healthy"}


__all__ = [
    "health_check",
]
