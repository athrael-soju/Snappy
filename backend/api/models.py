from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SearchItem(BaseModel):
    image_url: Optional[str]
    label: Optional[str]
    payload: Dict[str, Any]
    score: Optional[float] = None
    json_url: Optional[str] = None  # OCR JSON URL when available


class TokenInfo(BaseModel):
    """Information about a query token."""

    index: int
    token: str
    should_filter: bool  # Whether token should be filtered (stopword, punctuation, etc.)


class SimilarityMapResult(BaseModel):
    """Similarity map for a single token."""

    token_index: int
    token: str
    similarity_map_base64: str  # Base64-encoded PNG image with heatmap overlay


class SimilarityMapRequest(BaseModel):
    """Request for similarity map generation."""

    image_url: str  # URL of the image to analyze (from MinIO)
    query: str  # The search query text
    selected_tokens: Optional[List[int]] = None  # Token indices (None = all non-filtered)
    alpha: float = Field(default=0.5, ge=0.0, le=1.0)  # Blend factor


class SimilarityMapResponse(BaseModel):
    """Response containing similarity maps."""

    query: str
    tokens: List[TokenInfo]  # All tokens with filter info
    similarity_maps: List[SimilarityMapResult]  # Maps for selected tokens
