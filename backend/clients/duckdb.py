"""DuckDB analytics service client."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Dict, List, Optional

import config
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

if TYPE_CHECKING:  # pragma: no cover - hints only
    pass

logger = logging.getLogger(__name__)


class DuckDBClient:
    """Client for DuckDB analytics service."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: Optional[int] = None,
        enabled: Optional[bool] = None,
        batch_size: Optional[int] = None,
        retry_attempts: Optional[int] = None,
    ):
        """Initialize DuckDB service client.

        Args:
            base_url: DuckDB service URL
            timeout: Request timeout in seconds
            enabled: Enable/disable DuckDB storage
            batch_size: Number of pages to batch
            retry_attempts: Number of retry attempts
        """
        self.enabled = enabled if enabled is not None else bool(config.DUCKDB_ENABLED)
        default_base = config.DUCKDB_URL or "http://localhost:8300"
        self.base_url = (base_url or default_base).rstrip("/")
        self.timeout = timeout or int(config.DUCKDB_API_TIMEOUT)
        self.batch_size = batch_size or config.DUCKDB_BATCH_SIZE
        self.retry_attempts = retry_attempts or config.DUCKDB_RETRY_ATTEMPTS

        # Setup HTTP session with retry logic
        retry = Retry(
            total=self.retry_attempts,
            connect=self.retry_attempts,
            read=self.retry_attempts,
            status=self.retry_attempts,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods={"GET", "POST", "DELETE"},
            raise_on_status=False,
        )
        adapter = HTTPAdapter(
            max_retries=retry,
            pool_connections=10,
            pool_maxsize=10,
        )
        self.session = requests.Session()
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        self._closed = False

        logger.info(
            f"DuckDB service initialized (enabled={self.enabled}, url={self.base_url})"
        )

    def is_enabled(self) -> bool:
        """Check if DuckDB storage is enabled."""
        return self.enabled

    def health_check(self) -> bool:
        """Check if DuckDB service is healthy."""
        if not self.enabled:
            logger.debug("Skipping DuckDB health check: service disabled")
            return False

        try:
            response = self.session.get(f"{self.base_url}/health", timeout=self.timeout)
            response.raise_for_status()
            payload = response.json()
            return bool(payload.get("status") == "healthy")
        except Exception as exc:
            logger.warning(f"DuckDB health check failed: {exc}")
            return False

    def store_ocr_page(
        self,
        provider: str,
        version: str,
        filename: str,
        page_number: int,
        page_id: str,
        document_id: str,
        text: str,
        markdown: str,
        raw_text: Optional[str],
        regions: List[Dict[str, Any]],
        extracted_at: str,
        storage_url: str,
        pdf_page_index: Optional[int] = None,
        total_pages: Optional[int] = None,
        page_width_px: Optional[int] = None,
        page_height_px: Optional[int] = None,
        image_url: Optional[str] = None,
        image_storage: Optional[str] = None,
        extracted_images: Optional[List[Dict[str, Any]]] = None,
    ) -> bool:
        """Store OCR data for a single page.

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False

        try:
            payload = {
                "provider": provider,
                "version": version,
                "filename": filename,
                "page_number": page_number,
                "page_id": page_id,
                "text": text,
                "markdown": markdown,
                "raw_text": raw_text,
                "regions": regions or [],
                "extracted_at": extracted_at,
                "storage_url": storage_url,
                "document_id": document_id,
                "pdf_page_index": pdf_page_index,
                "total_pages": total_pages,
                "page_width_px": page_width_px,
                "page_height_px": page_height_px,
                "image_url": image_url,
                "image_storage": image_storage,
                "extracted_images": extracted_images or [],
            }

            response = self.session.post(
                f"{self.base_url}/ocr/store",
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()

            logger.debug(f"Stored OCR data in DuckDB: {filename} page {page_number}")
            return True

        except Exception as exc:
            logger.warning(
                f"Failed to store OCR data in DuckDB for {filename} page {page_number}: {exc}"
            )
            return False

    def store_ocr_batch(self, pages: List[Dict[str, Any]]) -> bool:
        """Store multiple OCR pages in a batch.

        Args:
            pages: List of OCR page data dictionaries

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled or not pages:
            return False

        try:
            payload = {"pages": pages}

            response = self.session.post(
                f"{self.base_url}/ocr/store/batch",
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()

            logger.info(f"Stored {len(pages)} OCR pages in DuckDB batch")
            return True

        except Exception as exc:
            logger.warning(f"Failed to store OCR batch in DuckDB: {exc}")
            return False

    def list_documents(
        self, limit: int = 100, offset: int = 0
    ) -> Optional[List[Dict[str, Any]]]:
        """List all indexed documents.

        Args:
            limit: Maximum number of documents to return
            offset: Number of documents to skip

        Returns:
            List of document info dictionaries or None on error
        """
        if not self.enabled:
            return None

        try:
            response = self.session.get(
                f"{self.base_url}/ocr/documents",
                params={"limit": limit, "offset": offset},
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()

        except Exception as exc:
            logger.warning(f"Failed to list documents from DuckDB: {exc}")
            return None

    def get_document(self, filename: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific document.

        Args:
            filename: Document filename

        Returns:
            Document info dictionary or None on error
        """
        if not self.enabled:
            return None

        try:
            response = self.session.get(
                f"{self.base_url}/ocr/documents/{filename}",
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()

        except Exception as exc:
            logger.warning(f"Failed to get document from DuckDB: {exc}")
            return None

    def get_page_regions(self, filename: str, page_number: int) -> Optional[List[Dict[str, Any]]]:
        """Get only regions for a specific page (optimized).

        This is more efficient than get_page() when only regions are needed.

        Args:
            filename: Document filename
            page_number: Page number

        Returns:
            List of region dictionaries or None on error
        """
        if not self.enabled:
            return None

        try:
            response = self.session.get(
                f"{self.base_url}/ocr/pages/{filename}/{page_number}/regions",
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()

        except Exception as exc:
            logger.warning(f"Failed to get page regions from DuckDB: {exc}")
            return None

    def get_page(self, filename: str, page_number: int) -> Optional[Dict[str, Any]]:
        """Get complete OCR data for a specific page.

        Use get_page_regions() instead if you only need regions for better performance.

        Args:
            filename: Document filename
            page_number: Page number

        Returns:
            Page data dictionary or None on error
        """
        if not self.enabled:
            return None

        try:
            response = self.session.get(
                f"{self.base_url}/ocr/pages/{filename}/{page_number}",
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()

        except Exception as exc:
            logger.warning(f"Failed to get page from DuckDB: {exc}")
            return None

    def delete_document(self, filename: str) -> bool:
        """Delete all data for a document.

        Args:
            filename: Document filename

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False

        try:
            response = self.session.delete(
                f"{self.base_url}/ocr/documents/{filename}",
                timeout=self.timeout,
            )
            response.raise_for_status()

            logger.info(f"Deleted document from DuckDB: {filename}")
            return True

        except Exception as exc:
            logger.warning(f"Failed to delete document from DuckDB: {exc}")
            return False

    def execute_query(
        self, query: str, limit: Optional[int] = None, timeout: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """Execute a SQL query with safety limits.

        Args:
            query: SQL query string
            limit: Maximum number of rows to return (default: 1000, max: 10000)
            timeout: Query timeout in seconds (overrides service default)

        Returns:
            Query result dictionary or None on error
        """
        if not self.enabled:
            return None

        # Apply default limit to prevent OOM
        if limit is None:
            limit = 1000  # Default limit
        elif limit > 10000:
            logger.warning(
                f"Query limit {limit} exceeds recommended maximum 10000, capping"
            )
            limit = 10000

        try:
            payload: Dict[str, Any] = {"query": query, "limit": limit}

            # Use custom timeout if provided
            request_timeout = timeout if timeout is not None else self.timeout

            response = self.session.post(
                f"{self.base_url}/query",
                json=payload,
                timeout=request_timeout,
            )
            response.raise_for_status()
            return response.json()

        except Exception as exc:
            logger.warning(f"Failed to execute query in DuckDB: {exc}")
            return None

    def get_stats(self) -> Optional[Dict[str, Any]]:
        """Get aggregate statistics.

        Returns:
            Statistics dictionary or None on error
        """
        if not self.enabled:
            return None

        try:
            response = self.session.get(
                f"{self.base_url}/stats",
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()

        except Exception as exc:
            logger.warning(f"Failed to get stats from DuckDB: {exc}")
            return None

    def check_document_exists(
        self, filename: str, file_size_bytes: Optional[int], total_pages: int
    ) -> Optional[Dict[str, Any]]:
        """Check if a document already exists in DuckDB.

        Args:
            filename: Document filename
            file_size_bytes: File size in bytes
            total_pages: Total number of pages

        Returns:
            Document info dictionary if exists, None otherwise
        """
        if not self.enabled:
            return None

        try:
            payload = {
                "filename": filename,
                "file_size_bytes": file_size_bytes,
                "total_pages": total_pages,
            }

            response = self.session.post(
                f"{self.base_url}/documents/check",
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            result = response.json()

            # Return None if document doesn't exist
            if not result or not result.get("exists"):
                return None

            return result.get("document")

        except Exception as exc:
            logger.warning(f"Failed to check document existence in DuckDB: {exc}")
            return None

    def store_document(
        self,
        document_id: str,
        filename: str,
        file_size_bytes: Optional[int],
        total_pages: int,
    ) -> bool:
        """Store document metadata in DuckDB.

        Args:
            document_id: UUID for this document
            filename: Document filename
            file_size_bytes: File size in bytes
            total_pages: Total number of pages

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False

        try:
            payload = {
                "document_id": document_id,
                "filename": filename,
                "file_size_bytes": file_size_bytes,
                "total_pages": total_pages,
            }

            response = self.session.post(
                f"{self.base_url}/documents/store",
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()

            logger.info(f"Stored document metadata in DuckDB: {filename}")
            return True

        except Exception as exc:
            logger.warning(f"Failed to store document in DuckDB: {exc}")
            return False

    def store_documents_batch(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Store multiple document metadata records in a batch.

        Args:
            documents: List of document metadata dictionaries with keys:
                - document_id: UUID for the document
                - filename: Document filename
                - file_size_bytes: File size in bytes
                - total_pages: Total number of pages

        Returns:
            Dict with 'success_count' and 'failed_count' keys
        """
        if not self.enabled or not documents:
            return {
                "success_count": 0,
                "failed_count": len(documents) if documents else 0,
            }

        try:
            payload = {"documents": documents}

            response = self.session.post(
                f"{self.base_url}/documents/store/batch",
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            result = response.json()

            success_count = result.get("success_count", len(documents))
            failed_count = result.get("failed_count", 0)

            logger.info(
                f"Stored {success_count} document metadata records in DuckDB batch "
                f"({failed_count} failures)"
            )
            return {"success_count": success_count, "failed_count": failed_count}

        except Exception as exc:
            logger.warning(f"Failed to store document batch in DuckDB: {exc}")
            return {"success_count": 0, "failed_count": len(documents)}

    def search_text(self, query: str, limit: int = 50) -> Optional[Dict[str, Any]]:
        """Search for text across all OCR data.

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            Search results dictionary or None on error
        """
        if not self.enabled:
            return None

        try:
            response = self.session.post(
                f"{self.base_url}/search/text",
                params={"q": query, "limit": limit},
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()

        except Exception as exc:
            logger.warning(f"Failed to search text in DuckDB: {exc}")
            return None

    # ------------------------------------------------------------------
    # Maintenance helpers
    # ------------------------------------------------------------------

    def initialize_storage(self) -> Optional[Dict[str, Any]]:
        """Ensure DuckDB storage is initialized."""
        return self._post_maintenance("initialize")

    def clear_storage(self) -> Optional[Dict[str, Any]]:
        """Clear all OCR data from DuckDB."""
        return self._post_maintenance("clear")

    def delete_storage(self) -> Optional[Dict[str, Any]]:
        """Delete/reset the DuckDB database file."""
        return self._post_maintenance("delete")

    def _post_maintenance(self, action: str) -> Optional[Dict[str, Any]]:
        if not self.enabled:
            return None
        try:
            response = self.session.post(
                f"{self.base_url}/maintenance/{action}",
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()
        except Exception as exc:
            logger.warning(f"DuckDB {action} maintenance failed: {exc}")
            return None

    def close(self):
        """Close the HTTP session safely."""
        if self._closed or not hasattr(self, "session"):
            return

        try:
            self.session.close()
            self._closed = True
            logger.debug("DuckDB HTTP session closed")
        except Exception as e:
            logger.warning(f"Error closing DuckDB session: {e}")

    def __del__(self):
        """Attempt cleanup on garbage collection."""
        try:
            self.close()
        except Exception:
            # Silently fail - resources will be cleaned up by OS
            # Don't log here as logging may not be available during shutdown
            pass

    def __enter__(self):
        """Context manager support."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Ensure cleanup with context manager."""
        self.close()
        return False
