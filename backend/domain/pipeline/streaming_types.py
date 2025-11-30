"""Data structures for streaming pipeline."""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from PIL import Image

if TYPE_CHECKING:
    from .image_processor import ProcessedImage


@dataclass
class PageBatch:
    """A batch of rasterized pages ready for processing."""

    document_id: str
    filename: str
    batch_id: int  # Batch sequence number within document
    page_start: int  # Starting page number (1-indexed)
    images: List[Image.Image]
    image_ids: List[str]  # Unique ID for each page (shared across all stages)
    metadata: List[Dict[str, Any]]  # Per-page metadata
    total_pages: int  # Total pages in document
    file_size_bytes: Optional[int] = None


@dataclass
class ProcessedBatch:
    """A batch with processed images ready for inline storage."""

    document_id: str
    filename: str
    batch_id: int
    page_start: int
    image_ids: List[str]
    metadata: List[Dict[str, Any]]
    total_pages: int
    # Processed images for inline storage
    full_images: List["ProcessedImage"] = field(default_factory=list)
    thumbnails: List["ProcessedImage"] = field(default_factory=list)


@dataclass
class EmbeddedBatch:
    """A batch with embeddings generated."""

    document_id: str
    filename: str
    batch_id: int
    page_start: int
    original_embeddings: List
    pooled_by_rows: Optional[List]
    pooled_by_columns: Optional[List]
    image_ids: List[str]
    metadata: List[Dict[str, Any]]
    # Processed images for inline storage (set by coordinator)
    full_images: List["ProcessedImage"] = field(default_factory=list)
    thumbnails: List["ProcessedImage"] = field(default_factory=list)
