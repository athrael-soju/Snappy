"""Data structures for streaming pipeline."""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from PIL import Image


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
