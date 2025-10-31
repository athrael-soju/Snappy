"""
API request and response models using Pydantic.
"""

from datetime import datetime
from typing import List

from pydantic import BaseModel, ConfigDict, Field


class OCRElement(BaseModel):
    """Flexible container for raw PaddleOCR-VL results."""

    model_config = ConfigDict(extra="allow")


class OCRResponse(BaseModel):
    """Response model for OCR extraction."""

    success: bool = Field(..., description="Whether the OCR processing was successful")
    message: str = Field(..., description="Status message")
    processing_time: float = Field(..., description="Processing time in seconds")
    results: List[OCRElement] = Field(
        default_factory=list, description="Raw PaddleOCR-VL results"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Response timestamp"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Document processed successfully",
                "processing_time": 5.23,
                "results": [
                    {
                        "type": "text",
                        "bbox": [10, 20, 100, 50],
                        "content": "Sample text",
                        "confidence": 0.98,
                    },
                    {
                        "type": "table",
                        "bbox": [120, 80, 300, 200],
                        "confidence": 0.92,
                        "structure": {"rows": 3, "cols": 4},
                    },
                ],
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
