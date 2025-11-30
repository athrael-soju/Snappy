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


class TokenSimilarityMap(BaseModel):
    """Similarity map for a single query token."""

    token: str  # The actual token text
    token_index: int  # Position in the query
    similarity_map: List[List[float]]  # [n_patches_x, n_patches_y]


class InterpretabilityResponse(BaseModel):
    """Response model for interpretability map generation."""

    query: str  # Original query text
    tokens: List[str]  # All query tokens (filtered)
    similarity_maps: List[TokenSimilarityMap]  # Per-token similarity maps
    n_patches_x: int  # Number of patches in x dimension
    n_patches_y: int  # Number of patches in y dimension
    image_width: int  # Original image width
    image_height: int  # Original image height
