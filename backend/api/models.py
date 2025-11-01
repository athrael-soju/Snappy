from typing import Any, Dict, List, Optional

from pydantic import BaseModel


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


class HeatmapResult(BaseModel):
    image_width: int
    image_height: int
    grid_rows: int
    grid_columns: int
    aggregate: str
    min_score: float
    max_score: float
    heatmap: List[List[float]]
