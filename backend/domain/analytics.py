import logging
from typing import Any, List, Optional

from clients.duckdb import DuckDBClient
from domain.errors import (
    DocumentNotFoundError,
    PageNotFoundError,
    QueryExecutionError,
    SearchError,
    StatisticsError,
)

logger = logging.getLogger(__name__)


def get_db_stats(duckdb_service: DuckDBClient) -> dict:
    """Get aggregate statistics from DuckDB.

    Args:
        duckdb_service: DuckDB client instance

    Returns:
        Dictionary containing statistics (total_documents, total_pages, total_regions, storage_size_mb)

    Raises:
        StatisticsError: If statistics cannot be retrieved
    """
    stats = duckdb_service.get_stats()
    if not stats:
        raise StatisticsError("Failed to retrieve statistics")
    return stats


def list_documents(
    duckdb_service: DuckDBClient, limit: int, offset: int
) -> List[dict]:
    """List all indexed documents in DuckDB.

    Args:
        duckdb_service: DuckDB client instance
        limit: Maximum number of documents to return
        offset: Number of documents to skip

    Returns:
        List of document dictionaries with metadata

    Raises:
        QueryExecutionError: If document list cannot be retrieved
    """
    documents = duckdb_service.list_documents(limit=limit, offset=offset)
    if documents is None:
        raise QueryExecutionError("Failed to retrieve documents")
    return documents


def get_document_info(duckdb_service: DuckDBClient, filename: str) -> dict:
    """Get information about a specific document.

    Args:
        duckdb_service: DuckDB client instance
        filename: Name of the document to retrieve

    Returns:
        Dictionary containing document metadata (filename, page_count, first_indexed, etc.)

    Raises:
        DocumentNotFoundError: If document does not exist
    """
    document = duckdb_service.get_document(filename)
    if not document:
        raise DocumentNotFoundError(f"Document '{filename}' not found")
    return document


def get_page_data(duckdb_service: DuckDBClient, filename: str, page_number: int) -> dict:
    """Get OCR data for a specific page from DuckDB.

    Args:
        duckdb_service: DuckDB client instance
        filename: Name of the document
        page_number: Page number to retrieve (0-indexed)

    Returns:
        Dictionary containing page OCR data (text, markdown, regions)

    Raises:
        PageNotFoundError: If page does not exist for the specified document
    """
    page = duckdb_service.get_page(filename, page_number)
    if not page:
        raise PageNotFoundError(f"Page {page_number} not found in document '{filename}'")
    return page


def delete_document_data(duckdb_service: DuckDBClient, filename: str) -> bool:
    """Delete all data for a document from DuckDB.

    Args:
        duckdb_service: DuckDB client instance
        filename: Name of the document to delete

    Returns:
        True if deletion was successful

    Raises:
        DocumentNotFoundError: If document does not exist or deletion fails
    """
    success = duckdb_service.delete_document(filename)
    if not success:
        raise DocumentNotFoundError(f"Document '{filename}' not found or deletion failed")
    return True


def execute_custom_query(
    duckdb_service: DuckDBClient, query: str, limit: int
) -> dict:
    """Execute a SQL query against DuckDB.

    Args:
        duckdb_service: DuckDB client instance
        query: SQL SELECT query to execute
        limit: Maximum number of rows to return

    Returns:
        Dictionary containing query results (columns, rows, row_count, query)

    Raises:
        QueryExecutionError: If query execution fails

    Note:
        Only SELECT queries are allowed. Dangerous operations are blocked.
    """
    result = duckdb_service.execute_query(query, limit)
    if not result:
        raise QueryExecutionError("Query execution failed")
    return result


def search_text_content(
    duckdb_service: DuckDBClient, query: str, limit: int
) -> List[dict]:
    """Full-text search across all OCR data.

    Args:
        duckdb_service: DuckDB client instance
        query: Search query string
        limit: Maximum number of results to return

    Returns:
        List of matching page dictionaries with search results

    Raises:
        SearchError: If search operation fails
    """
    results = duckdb_service.search_text(query, limit)
    if results is None:
        raise SearchError("Search failed")
    return results
