from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class RetrievedPage(BaseModel):
    image_url: Optional[str]
    label: Optional[str]
    payload: Dict[str, Any]
    score: Optional[float] = None


class SearchItem(BaseModel):
    image_url: Optional[str]
    label: Optional[str]
    payload: Dict[str, Any]
    score: Optional[float] = None


class OCRElement(BaseModel):
    index: int
    content: Dict[str, Any]
    metadata: Dict[str, Any] = Field(default_factory=dict)


class OCRExtractionResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    success: bool
    message: Optional[str] = None
    processing_time: Optional[float] = None
    elements: List[OCRElement] = Field(default_factory=list)
    markdown: Optional[str] = None
    timestamp: Optional[datetime] = None


class OCRHealthResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    status: str
    service: Optional[str] = None
    version: Optional[str] = None
    gpu_enabled: Optional[bool] = None
    pipeline_ready: Optional[bool] = None
    timestamp: Optional[datetime] = None
