"""
Pydantic models for request/response validation.
"""

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class ProcessingMode(str, Enum):
    """Available processing modes for DeepSeek OCR."""

    GUNDAM = "Gundam"
    TINY = "Tiny"
    SMALL = "Small"
    BASE = "Base"
    LARGE = "Large"


class TaskType(str, Enum):
    """Available task types for DeepSeek OCR."""

    MARKDOWN = "markdown"
    PLAIN_OCR = "plain_ocr"
    LOCATE = "locate"
    DESCRIBE = "describe"
    CUSTOM = "custom"


class OCRRequest(BaseModel):
    """Request model for OCR operations."""

    mode: ProcessingMode = Field(
        default=ProcessingMode.GUNDAM,
        description="Processing mode (affects quality/speed tradeoff)",
    )
    task: TaskType = Field(
        default=TaskType.MARKDOWN, description="Type of OCR task to perform"
    )
    custom_prompt: Optional[str] = Field(
        default=None,
        description="Custom prompt (required for 'custom' and 'locate' tasks)",
    )
    include_grounding: bool = Field(
        default=True, description="Include bounding box information in response"
    )
    include_images: bool = Field(
        default=True, description="Extract and embed images from document"
    )


class BoundingBox(BaseModel):
    """Bounding box coordinates."""

    x1: int
    y1: int
    x2: int
    y2: int
    label: str


class OCRResponse(BaseModel):
    """Response model for OCR operations."""

    text: str = Field(description="Extracted text with grounding references")
    markdown: Optional[str] = Field(
        default=None, description="Cleaned markdown output with embedded images"
    )
    raw: str = Field(description="Raw model output")
    bounding_boxes: List[BoundingBox] = Field(
        default_factory=list, description="List of detected bounding boxes"
    )
    crops: List[str] = Field(
        default_factory=list, description="Base64-encoded cropped images"
    )
    annotated_image: Optional[str] = Field(
        default=None, description="Base64-encoded image with bounding boxes"
    )


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    model: str
    device: str
    torch_dtype: str


class InfoResponse(BaseModel):
    """Model information response."""

    model: str
    device: str
    modes: List[str]
    tasks: List[str]
    model_configs: dict
