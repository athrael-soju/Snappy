"""DuckDB service HTTP client for storing and querying OCR data."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)


class DuckDBService:
    """
    HTTP client for DuckDB service API.

    Communicates with standalone DuckDB service for structured OCR data storage,
    enabling quantitative searching and analytics on processed documents.
    """

    def __init__(
        self,
        base_url: str,
        enabled: bool = True,
        timeout: int = 30,
    ):
        """
        Initialize DuckDB service client.

        Args:
            base_url: Base URL of DuckDB service (e.g., http://duckdb:8300)
            enabled: Whether DuckDB storage is enabled
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.enabled = enabled
        self.timeout = timeout
        self.session = requests.Session()

        if self.enabled:
            self._check_health()

    def _check_health(self) -> None:
        """Check if DuckDB service is accessible."""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            logger.info(f"DuckDB service connected: {data}")
        except Exception as e:
            logger.warning(f"DuckDB service health check failed: {e}")
            # Don't disable completely, allow retry on actual operations

    def store_ocr_result(
        self,
        payload: Dict[str, Any],
    ) -> Optional[int]:
        """
        Store OCR result in DuckDB via HTTP API.

        Args:
            payload: OCR result payload from storage handler

        Returns:
            ID of inserted record or None if disabled/failed
        """
        if not self.enabled:
            return None

        try:
            response = self.session.post(
                f"{self.base_url}/ocr/store", json=payload, timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()

            ocr_result_id = result.get("ocr_result_id")
            logger.debug(
                f"Stored OCR result in DuckDB: {payload.get('filename')} "
                f"page {payload.get('page_number')} (id={ocr_result_id})"
            )

            return ocr_result_id

        except Exception as e:
            logger.error(f"Failed to store OCR result in DuckDB: {e}", exc_info=True)
            return None

    def search_text(
        self,
        query: str,
        limit: int = 10,
        filename_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Full-text search across OCR results.

        Args:
            query: Search query string
            limit: Maximum number of results
            filename_filter: Optional filename pattern to filter by

        Returns:
            List of matching OCR results
        """
        if not self.enabled:
            return []

        try:
            response = self.session.post(
                f"{self.base_url}/ocr/search",
                json={
                    "query": query,
                    "limit": limit,
                    "filename_filter": filename_filter,
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()

            return data.get("results", [])

        except Exception as e:
            logger.error(f"Failed to search OCR text in DuckDB: {e}")
            return []

    def get_document_stats(
        self,
        filename: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get statistics about stored OCR data.

        Args:
            filename: Optional filename to get stats for specific document

        Returns:
            Dictionary with statistics
        """
        if not self.enabled:
            return {}

        try:
            response = self.session.post(
                f"{self.base_url}/ocr/stats",
                json={"filename": filename},
                timeout=self.timeout,
            )
            response.raise_for_status()

            return response.json()

        except Exception as e:
            logger.error(f"Failed to get document stats from DuckDB: {e}")
            return {}

    def get_ocr_result(
        self,
        filename: str,
        page_number: int,
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch OCR result for a specific page.

        Args:
            filename: Document filename
            page_number: Page number

        Returns:
            OCR result dictionary or None if not found
        """
        if not self.enabled:
            return None

        try:
            response = self.session.get(
                f"{self.base_url}/ocr/result/{filename}/{page_number}",
                timeout=self.timeout,
            )

            if response.status_code == 404:
                return None

            response.raise_for_status()
            return response.json()

        except Exception as e:
            logger.debug(
                f"OCR result not available for {filename} page {page_number}: {e}"
            )
            return None

    def health_check(self) -> bool:
        """
        Check if DuckDB service is healthy.

        Returns:
            True if service is accessible and working
        """
        if not self.enabled:
            return False

        try:
            response = self.session.get(f"{self.base_url}/health", timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            return data.get("status") == "healthy"

        except Exception as e:
            logger.error(f"DuckDB health check failed: {e}")
            return False

    def close(self) -> None:
        """Close HTTP session."""
        if hasattr(self, "session"):
            try:
                self.session.close()
                logger.info("DuckDB HTTP session closed")
            except Exception as e:
                logger.error(f"Error closing DuckDB session: {e}")

    def __del__(self):
        """Ensure session is closed on garbage collection."""
        self.close()
