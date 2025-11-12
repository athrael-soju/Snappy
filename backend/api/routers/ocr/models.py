from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


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


__all__ = [
    "OcrBatchRequest",
    "OcrBatchResponse",
    "OcrDocumentRequest",
    "OcrPageRequest",
    "OcrResponse",
]
