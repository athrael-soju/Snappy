"""
API request and response models using Pydantic.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class OCRElement(BaseModel):
    """Represents a single OCR element (text, table, chart, formula, etc.)."""

    index: int = Field(..., description="Element index in the document")
    content: Dict[str, Any] = Field(
        ..., description="Element content (text, structure, etc.)"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Element metadata (bbox, confidence, type, etc.)",
    )


class OCRResponse(BaseModel):
    """Response model for OCR extraction."""

    success: bool = Field(..., description="Whether the OCR processing was successful")
    message: str = Field(..., description="Status message")
    processing_time: float = Field(..., description="Processing time in seconds")
    elements: List[OCRElement] = Field(
        default_factory=list, description="Extracted OCR elements"
    )
    markdown: Optional[str] = Field(None, description="Markdown formatted output")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Response timestamp"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Document processed successfully",
                "processing_time": 5.23,
                "elements": [
                    {
                        "index": 0,
                        "content": {"text": "Sample document text", "type": "text"},
                        "metadata": {"bbox": [10, 20, 100, 50], "confidence": 0.98},
                    }
                ],
                "markdown": "# Document OCR Results\n\n## Element 1\n\n**text**: Sample document text",
                "timestamp": "2025-01-15T10:30:00Z",
            }
        }


class HealthResponse(BaseModel):
    """Response model for health check."""

    status: str = Field(..., description="Service status (healthy/unhealthy)")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    gpu_enabled: bool = Field(..., description="Whether GPU is enabled")
    pipeline_ready: bool = Field(..., description="Whether OCR pipeline is initialized")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Response timestamp"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "service": "PaddleOCR-VL Service",
                "version": "1.0.0",
                "gpu_enabled": True,
                "pipeline_ready": True,
                "timestamp": "2025-01-15T10:30:00Z",
            }
        }


class ErrorResponse(BaseModel):
    """Response model for errors."""

    success: bool = Field(False, description="Always False for errors")
    message: str = Field(..., description="Error message")
    error_type: str = Field(..., description="Error type/category")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Error timestamp"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "message": "Invalid file format. Only images and PDFs are supported.",
                "error_type": "ValidationError",
                "timestamp": "2025-01-15T10:30:00Z",
            }
        }
