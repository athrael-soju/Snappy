from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel, Field
from services.paddleocr import PaddleOCRService

from ..dependencies import get_paddleocr_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ocr", tags=["paddle-ocr"])


class PaddleOCRLayoutResponse(BaseModel):
    """Response model returned by the layout parsing endpoint."""

    lines: List[str] = Field(
        default_factory=list,
        description="Flattened list of recognised text segments extracted from the response.",
    )
    full_text: str = Field(
        "",
        description="Convenience aggregation of recognised text (newline separated).",
    )
    raw: Dict[str, Any] = Field(
        default_factory=dict,
        description="Raw JSON payload returned from PaddleOCR for advanced consumers.",
    )


def _parse_options(options: Optional[str]) -> Optional[Dict[str, Any]]:
    if not options:
        return None
    try:
        parsed = json.loads(options)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid JSON payload for 'options': {exc}",
        ) from exc

    if not isinstance(parsed, dict):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="'options' must decode to a JSON object",
        )
    return parsed


@router.post(
    "/layout-parsing",
    response_model=PaddleOCRLayoutResponse,
    summary="Run PaddleOCR layout parsing on an uploaded document page.",
)
async def layout_parsing(
    file: UploadFile = File(..., description="Image or PDF page to analyse."),
    file_type: int = Form(
        1,
        description=(
            "Media type expected by the PaddleOCR server. "
            "Defaults to 1 (image). Refer to PaddleOCR documentation for other values."
        ),
    ),
    options: Optional[str] = Form(
        None,
        description=(
            "Optional JSON string with extra parameters forwarded to PaddleOCR. "
            'Example: \'{"language":"en"}\''
        ),
    ),
    service: PaddleOCRService = Depends(get_paddleocr_service),
) -> PaddleOCRLayoutResponse:
    """
    Forward the uploaded file to the PaddleOCR container, returning recognised text.

    The PaddleOCR service expects base64-encoded file content and a file type flag.
    Additional advanced arguments can be provided via the ``options`` form field.
    """
    payload = await file.read()
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    forwarded_options = _parse_options(options)

    try:
        raw = service.layout_parsing(
            payload,
            file_type=file_type,
            options=forwarded_options,
        )
        lines = service.extract_text(raw)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("PaddleOCR inference failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"PaddleOCR inference failed: {exc}",
        ) from exc

    return PaddleOCRLayoutResponse(
        lines=lines,
        full_text="\n".join(lines),
        raw=raw,
    )
