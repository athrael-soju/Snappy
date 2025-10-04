"""Data models for ingestion pipeline."""

from typing import List, Optional, Literal
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class StageType(str, Enum):
    """Pipeline stage types."""
    QUEUED = "queued"
    INTAKE = "intake"
    IMAGE = "image"
    EMBED = "embed"
    INDEX = "index"
    STORAGE = "storage"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class IngestionJob:
    """Represents an ingestion job."""
    job_id: str
    files: List[str]  # Original filenames
    created_at: datetime
    status: Literal["queued", "running", "completed", "failed", "cancelled"] = "queued"
    
    def to_dict(self) -> dict:
        return {
            "job_id": self.job_id,
            "files": self.files,
            "created_at": self.created_at.isoformat(),
            "status": self.status,
        }


@dataclass
class PageRef:
    """Reference to a specific page within a file."""
    job_id: str
    file_id: str
    page_index: int  # 0-based
    total_pages: int
    
    def to_dict(self) -> dict:
        return {
            "job_id": self.job_id,
            "file_id": self.file_id,
            "page_index": self.page_index,
            "total_pages": self.total_pages,
        }


@dataclass
class BatchRef:
    """Reference to a batch of pages."""
    job_id: str
    file_id: str
    page_indices: List[int]  # 0-based indices
    
    def to_dict(self) -> dict:
        return {
            "job_id": self.job_id,
            "file_id": self.file_id,
            "page_indices": self.page_indices,
        }


@dataclass
class ProgressEvent:
    """Progress event for SSE streaming."""
    job_id: str
    stage: StageType
    file_id: Optional[str] = None
    counts: dict = field(default_factory=dict)
    message: Optional[str] = None
    error: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "job_id": self.job_id,
            "stage": self.stage.value,
            "file_id": self.file_id,
            "counts": self.counts,
            "message": self.message,
            "error": self.error,
        }


@dataclass
class PageData:
    """Data for a single page including image and metadata."""
    job_id: str
    file_id: str
    page_index: int
    total_pages: int
    image_path: str  # Temp file path
    filename: str
    file_size_bytes: Optional[int] = None
    page_width_px: Optional[int] = None
    page_height_px: Optional[int] = None
    document_id: Optional[str] = None  # Set during storage stage
    image_url: Optional[str] = None  # Set during storage stage
    
    def to_metadata(self) -> dict:
        """Convert to metadata dict for indexing."""
        return {
            "filename": self.filename,
            "file_size_bytes": self.file_size_bytes,
            "pdf_page_index": self.page_index + 1,  # 1-based for display
            "total_pages": self.total_pages,
            "page_width_px": self.page_width_px,
            "page_height_px": self.page_height_px,
        }


@dataclass
class EmbeddingData:
    """Embedding result with metadata."""
    page_data: PageData
    original_embedding: List[float]
    pooled_rows: Optional[List[float]] = None
    pooled_cols: Optional[List[float]] = None
    
    def to_dict(self) -> dict:
        return {
            "page_data": self.page_data.to_metadata(),
            "has_pooled": self.pooled_rows is not None,
        }
