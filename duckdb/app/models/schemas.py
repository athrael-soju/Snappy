"""Pydantic models shared across the DuckDB API."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    database: str
    version: str


class InfoResponse(BaseModel):
    version: str
    database_path: str
    database_size_mb: float
    tables: Dict[str, int]


class OcrPageData(BaseModel):
    """OCR payload for a single page."""

    provider: str
    version: str
    filename: str
    page_number: int
    text: str
    markdown: str
    raw_text: Optional[str] = None
    regions: List[Dict[str, Any]] = Field(default_factory=list)
    extracted_at: str
    storage_url: str
    document_id: Optional[str] = None
    pdf_page_index: Optional[int] = None
    total_pages: Optional[int] = None
    page_width_px: Optional[int] = None
    page_height_px: Optional[int] = None
    image_url: Optional[str] = None
    image_storage: Optional[str] = None
    extracted_images: List[Dict[str, Any]] = Field(default_factory=list)


class OcrBatchData(BaseModel):
    pages: List[OcrPageData]


class QueryRequest(BaseModel):
    query: str
    limit: Optional[int] = Field(default=1000, le=10000)


class QueryResponse(BaseModel):
    columns: List[str]
    rows: List[List[Any]]
    row_count: int
    query: str


class StatsResponse(BaseModel):
    total_documents: int
    total_pages: int
    total_regions: int
    storage_size_mb: float
    schema_active: bool


class DocumentInfo(BaseModel):
    filename: str
    page_count: int
    first_indexed: str
    last_indexed: str
    total_regions: int


class DocumentCheckRequest(BaseModel):
    """Request to check if a document exists."""

    filename: str
    file_size_bytes: Optional[int]
    total_pages: int


class DocumentStoreRequest(BaseModel):
    """Request to store document metadata."""

    document_id: str
    filename: str
    file_size_bytes: Optional[int]
    total_pages: int


class DocumentStoreBatchRequest(BaseModel):
    """Request to store multiple document metadata records."""

    documents: List[DocumentStoreRequest]
