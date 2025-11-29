from typing import Any, Dict, Optional

from pydantic import BaseModel


class SearchItem(BaseModel):
    image_url: Optional[str]
    label: Optional[str]
    payload: Dict[str, Any]
    score: Optional[float] = None
    json_url: Optional[str] = None  # OCR JSON URL when available


class HeatmapResponse(BaseModel):
    """Response for on-demand heatmap generation."""

    heatmap_url: str  # Base64 data URL of the heatmap image
    width: int
    height: int
