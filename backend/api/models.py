from typing import Any, Dict, Optional

from pydantic import BaseModel


class SearchItem(BaseModel):
    image_url: Optional[str]
    label: Optional[str]
    payload: Dict[str, Any]
    score: Optional[float] = None
    json_url: Optional[str] = None  # OCR JSON URL when available
    heatmap_url: Optional[str] = None  # Attention heatmap data URL when enabled
