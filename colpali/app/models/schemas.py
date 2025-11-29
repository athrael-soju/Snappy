"""Pydantic models for request/response validation."""

from typing import List, Optional, Union

from pydantic import BaseModel


class QueryRequest(BaseModel):
    """Request model for query embedding generation."""

    queries: Union[str, List[str]]


class QueryEmbeddingResponse(BaseModel):
    """Response model for query embeddings."""

    embeddings: List[List[List[float]]]


class Dimension(BaseModel):
    """Image dimension specification."""

    width: int
    height: int


class PatchResult(BaseModel):
    """Result of patch calculation for a single image dimension."""

    width: int
    height: int
    n_patches_x: Optional[int] = None
    n_patches_y: Optional[int] = None
    error: Optional[str] = None


class PatchRequest(BaseModel):
    """Request model for patch calculation."""

    dimensions: List[Dimension]


class PatchBatchResponse(BaseModel):
    """Response model for batch patch calculation."""

    results: List[PatchResult]


class ImageEmbeddingItem(BaseModel):
    """Single image's embeddings and image-token boundaries."""

    embedding: List[List[float]]  # [sequence_length, hidden_dim]
    image_patch_start: int  # index where image tokens begin
    image_patch_len: int  # number of image tokens (should equal x_patches * y_patches)
    image_patch_indices: List[int]  # explicit positions of every image token


class ImageEmbeddingBatchResponse(BaseModel):
    """Response model for batch image embeddings."""

    embeddings: List[ImageEmbeddingItem]


class SimilarityMapRequest(BaseModel):
    """Request model for similarity map generation."""

    query: str
    selected_tokens: Optional[List[int]] = None  # Token indices to generate maps for (None = all)


class TokenInfo(BaseModel):
    """Information about a query token."""

    index: int
    token: str
    should_filter: bool  # Whether this token should be filtered out (stopword, punctuation, etc.)


class SimilarityMapResult(BaseModel):
    """Similarity map for a single token."""

    token_index: int
    token: str
    similarity_map_base64: str  # Base64-encoded PNG image with heatmap overlay


class SimilarityMapResponse(BaseModel):
    """Response model for similarity map generation."""

    query: str
    tokens: List[TokenInfo]  # All tokens with filter info
    similarity_maps: List[SimilarityMapResult]  # Maps for selected tokens
