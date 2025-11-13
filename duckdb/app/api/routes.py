"""API routes for the DuckDB analytics service."""

from __future__ import annotations

from typing import Any, Dict, List

from app.core.config import settings
from app.core.logging import logger
from app.models.schemas import (
    DocumentCheckRequest,
    DocumentInfo,
    DocumentStoreRequest,
    HealthResponse,
    InfoResponse,
    OcrBatchData,
    OcrPageData,
    QueryRequest,
    QueryResponse,
    StatsResponse,
)
from app.services import duckdb_service
from fastapi import APIRouter, HTTPException, Query

router = APIRouter()


@router.get("/", response_model=Dict[str, str])
async def root() -> Dict[str, str]:
    """Root endpoint for quick info."""
    return {
        "service": "DuckDB Analytics Service",
        "version": settings.API_VERSION,
        "description": "Columnar analytics storage for OCR data",
    }


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    healthy = duckdb_service.health()
    if not healthy:
        raise HTTPException(status_code=503, detail="Database unhealthy")
    return HealthResponse(
        status="healthy", database="connected", version=settings.API_VERSION
    )


@router.get("/info", response_model=InfoResponse)
async def get_info() -> InfoResponse:
    """Return database info and table counts."""
    try:
        return duckdb_service.info()
    except Exception as exc:
        logger.error("Failed to fetch info: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/ocr/store", response_model=Dict[str, Any])
async def store_ocr_page(data: OcrPageData) -> Dict[str, Any]:
    """Store OCR data for a single page."""
    try:
        return duckdb_service.store_page(data)
    except Exception as exc:
        logger.error("Failed to store OCR page: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/ocr/store/batch", response_model=Dict[str, Any])
async def store_ocr_batch(data: OcrBatchData) -> Dict[str, Any]:
    """Store a batch of OCR pages."""
    try:
        return duckdb_service.store_batch(data)
    except Exception as exc:
        logger.error("Failed to store OCR batch: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/ocr/documents", response_model=List[DocumentInfo])
async def list_documents(
    limit: int = Query(default=100, le=1000),
    offset: int = Query(default=0, ge=0),
) -> List[DocumentInfo]:
    """List indexed documents."""
    try:
        return duckdb_service.list_documents(limit=limit, offset=offset)
    except Exception as exc:
        logger.error("Failed to list documents: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/ocr/documents/{filename}", response_model=DocumentInfo)
async def get_document(filename: str) -> DocumentInfo:
    """Get info about a single document."""
    try:
        return duckdb_service.get_document(filename)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        logger.error("Failed to get document: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/ocr/pages/{filename}/{page_number}", response_model=Dict[str, Any])
async def get_page(filename: str, page_number: int) -> Dict[str, Any]:
    """Fetch OCR data for a specific page."""
    try:
        return duckdb_service.get_page(filename, page_number)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        logger.error("Failed to get page: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.delete("/ocr/documents/{filename}", response_model=Dict[str, Any])
async def delete_document(filename: str) -> Dict[str, Any]:
    """Delete all data for a document."""
    try:
        return duckdb_service.delete_document(filename)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        logger.error("Failed to delete document: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/documents/check", response_model=Dict[str, Any])
async def check_document_exists(request: DocumentCheckRequest) -> Dict[str, Any]:
    """Check if a document already exists in the database."""
    try:
        doc = duckdb_service.check_document_exists(
            request.filename, request.file_size_bytes, request.total_pages
        )
        if doc:
            return {"exists": True, "document": doc}
        return {"exists": False, "document": None}
    except Exception as exc:
        logger.error("Failed to check document existence: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/documents/store", response_model=Dict[str, Any])
async def store_document(request: DocumentStoreRequest) -> Dict[str, Any]:
    """Store or update document metadata."""
    try:
        db_id = duckdb_service.store_document(
            document_id=request.document_id,
            filename=request.filename,
            file_size_bytes=request.file_size_bytes,
            total_pages=request.total_pages,
        )
        return {
            "status": "success",
            "message": "Document metadata stored",
            "document_db_id": db_id,
        }
    except Exception as exc:
        logger.error("Failed to store document: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/query", response_model=QueryResponse)
async def execute_query(request: QueryRequest) -> QueryResponse:
    """Execute a read-only SQL query."""
    try:
        return duckdb_service.run_query(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error("Query execution failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/stats", response_model=StatsResponse)
async def get_stats() -> StatsResponse:
    """Return aggregate statistics."""
    try:
        return duckdb_service.stats()
    except Exception as exc:
        logger.error("Failed to fetch stats: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/search/text", response_model=QueryResponse)
async def search_text(
    q: str = Query(..., description="Search query"),
    limit: int = Query(default=50, le=500),
) -> QueryResponse:
    """Full-text search across OCR text."""
    try:
        return duckdb_service.search_text(query=q, limit=limit)
    except Exception as exc:
        logger.error("Failed to run search: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/maintenance/initialize", response_model=Dict[str, Any])
async def maintenance_initialize() -> Dict[str, Any]:
    """Ensure DuckDB is ready for use."""
    try:
        return duckdb_service.initialize_storage()
    except Exception as exc:
        logger.error("DuckDB initialization check failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/maintenance/clear", response_model=Dict[str, Any])
async def maintenance_clear() -> Dict[str, Any]:
    """Delete all OCR data from DuckDB while keeping the schema."""
    try:
        return duckdb_service.clear_storage()
    except Exception as exc:
        logger.error("DuckDB clear failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/maintenance/delete", response_model=Dict[str, Any])
async def maintenance_delete() -> Dict[str, Any]:
    """Reset the DuckDB database file."""
    try:
        return duckdb_service.delete_storage()
    except Exception as exc:
        logger.error("DuckDB delete failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))
