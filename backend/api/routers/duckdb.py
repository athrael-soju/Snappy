"""DuckDB analytics endpoints."""

import logging
from typing import Any, List, Optional

from api.dependencies import get_duckdb_service
from domain.analytics import (
    delete_document_data,
    execute_custom_query,
    get_db_stats,
    get_document_info,
    get_page_data,
    list_documents as list_docs_domain,
    search_text_content,
)
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from clients.duckdb import DuckDBClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/duckdb", tags=["duckdb"])


# Request/Response Models
class QueryRequest(BaseModel):
    """SQL query request."""

    query: str = Field(..., description="SQL query to execute")
    limit: Optional[int] = Field(
        default=1000, le=10000, description="Maximum rows to return"
    )


class QueryResponse(BaseModel):
    """SQL query response."""

    columns: List[str]
    rows: List[List[Any]]
    row_count: int
    query: str


class StatsResponse(BaseModel):
    """Database statistics."""

    total_documents: int
    total_pages: int
    total_regions: int
    storage_size_mb: float


class DocumentInfo(BaseModel):
    """Document information."""

    filename: str
    page_count: int
    first_indexed: str
    last_indexed: str
    total_regions: int


# Endpoints


@router.get("/health")
async def health_check(
    duckdb_service: Optional[DuckDBClient] = Depends(get_duckdb_service),
):
    """Check DuckDB service health."""
    if not duckdb_service:
        raise HTTPException(
            status_code=503, detail="DuckDB service is not enabled or available"
        )

    is_healthy = duckdb_service.health_check()
    if not is_healthy:
        raise HTTPException(status_code=503, detail="DuckDB service is unhealthy")

    return {"status": "healthy"}


@router.get("/stats", response_model=StatsResponse)
async def get_stats(
    duckdb_service: Optional[DuckDBClient] = Depends(get_duckdb_service),
):
    """Get aggregate statistics from DuckDB."""
    if not duckdb_service:
        raise HTTPException(
            status_code=503, detail="DuckDB service is not enabled or available"
        )

    stats = get_db_stats(duckdb_service)
    return StatsResponse(**stats)


@router.get("/documents", response_model=List[DocumentInfo])
async def list_documents(
    limit: int = Query(default=100, le=1000, description="Maximum results"),
    offset: int = Query(default=0, ge=0, description="Results offset"),
    duckdb_service: Optional[DuckDBClient] = Depends(get_duckdb_service),
):
    """List all indexed documents in DuckDB."""
    if not duckdb_service:
        raise HTTPException(
            status_code=503, detail="DuckDB service is not enabled or available"
        )

    documents = list_docs_domain(duckdb_service, limit, offset)
    return [DocumentInfo(**doc) for doc in documents]


@router.get("/documents/{filename}", response_model=DocumentInfo)
async def get_document(
    filename: str,
    duckdb_service: Optional[DuckDBClient] = Depends(get_duckdb_service),
):
    """Get information about a specific document."""
    if not duckdb_service:
        raise HTTPException(
            status_code=503, detail="DuckDB service is not enabled or available"
        )

    document = get_document_info(duckdb_service, filename)
    return DocumentInfo(**document)


@router.get("/pages/{filename}/{page_number}")
async def get_page(
    filename: str,
    page_number: int,
    duckdb_service: Optional[DuckDBClient] = Depends(get_duckdb_service),
):
    """Get OCR data for a specific page from DuckDB."""
    if not duckdb_service:
        raise HTTPException(
            status_code=503, detail="DuckDB service is not enabled or available"
        )

    return get_page_data(duckdb_service, filename, page_number)


@router.delete("/documents/{filename}")
async def delete_document(
    filename: str,
    duckdb_service: Optional[DuckDBClient] = Depends(get_duckdb_service),
):
    """Delete all data for a document from DuckDB."""
    if not duckdb_service:
        raise HTTPException(
            status_code=503, detail="DuckDB service is not enabled or available"
        )

    delete_document_data(duckdb_service, filename)
    return {"status": "success", "filename": filename}


@router.post("/query", response_model=QueryResponse)
async def execute_query(
    request: QueryRequest,
    duckdb_service: Optional[DuckDBClient] = Depends(get_duckdb_service),
):
    """Execute a SQL query against DuckDB.

    Note: Only SELECT queries are allowed. Dangerous operations are blocked.
    """
    if not duckdb_service:
        raise HTTPException(
            status_code=503, detail="DuckDB service is not enabled or available"
        )

    result = execute_custom_query(duckdb_service, request.query, request.limit)
    return QueryResponse(**result)


@router.post("/search")
async def search_text(
    q: str = Query(..., description="Search query"),
    limit: int = Query(default=50, le=500, description="Maximum results"),
    duckdb_service: Optional[DuckDBClient] = Depends(get_duckdb_service),
):
    """Full-text search across all OCR data."""
    if not duckdb_service:
        raise HTTPException(
            status_code=503, detail="DuckDB service is not enabled or available"
        )

    return search_text_content(duckdb_service, q, limit)
