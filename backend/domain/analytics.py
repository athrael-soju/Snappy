import logging
from typing import Any, List, Optional

from api.dependencies import get_duckdb_service
from clients.duckdb import DuckDBClient
from fastapi import HTTPException

logger = logging.getLogger(__name__)


def get_db_stats(duckdb_service: DuckDBClient) -> dict:
    """Get aggregate statistics from DuckDB."""
    stats = duckdb_service.get_stats()
    if not stats:
        raise HTTPException(status_code=500, detail="Failed to retrieve statistics")
    return stats


def list_documents(
    duckdb_service: DuckDBClient, limit: int, offset: int
) -> List[dict]:
    """List all indexed documents in DuckDB."""
    documents = duckdb_service.list_documents(limit=limit, offset=offset)
    if documents is None:
        raise HTTPException(status_code=500, detail="Failed to retrieve documents")
    return documents


def get_document_info(duckdb_service: DuckDBClient, filename: str) -> dict:
    """Get information about a specific document."""
    document = duckdb_service.get_document(filename)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


def get_page_data(duckdb_service: DuckDBClient, filename: str, page_number: int) -> dict:
    """Get OCR data for a specific page from DuckDB."""
    page = duckdb_service.get_page(filename, page_number)
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    return page


def delete_document_data(duckdb_service: DuckDBClient, filename: str) -> bool:
    """Delete all data for a document from DuckDB."""
    success = duckdb_service.delete_document(filename)
    if not success:
        raise HTTPException(
            status_code=404, detail="Document not found or deletion failed"
        )
    return True


def execute_custom_query(
    duckdb_service: DuckDBClient, query: str, limit: int
) -> dict:
    """Execute a SQL query against DuckDB."""
    result = duckdb_service.execute_query(query, limit)
    if not result:
        raise HTTPException(status_code=400, detail="Query execution failed")
    return result


def search_text_content(
    duckdb_service: DuckDBClient, query: str, limit: int
) -> List[dict]:
    """Full-text search across all OCR data."""
    results = duckdb_service.search_text(query, limit)
    if not results:
        raise HTTPException(status_code=500, detail="Search failed")
    return results
