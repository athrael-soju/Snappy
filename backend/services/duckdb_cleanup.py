"""DuckDB cleanup operations for job cancellation."""

import logging
from typing import Dict, List

from services.duckdb import DuckDBService

logger = logging.getLogger(__name__)


class DuckDBCleanupService:
    """Service for cleaning up DuckDB data by job_id.

    Implements the CleanupService protocol for DuckDB storage.

    This service deletes records from both the documents and pages tables
    that are associated with a specific job_id.
    """

    def __init__(self, duckdb_service: DuckDBService):
        """Initialize DuckDB cleanup service.

        Args:
            duckdb_service: DuckDB service instance
        """
        self.service = duckdb_service

    def cleanup_by_job_id(self, job_id: str) -> Dict[str, any]:
        """Remove all records associated with a job_id.

        Deletes from:
        - documents table
        - pages table (OCR data)

        Args:
            job_id: The job identifier to clean up

        Returns:
            Dict with cleanup statistics
        """
        if not job_id:
            return {
                "service": "duckdb",
                "deleted_count": 0,
                "errors": ["Empty job_id provided"],
                "success": False,
            }

        if not self.service.is_enabled():
            logger.debug("DuckDB service is disabled, skipping cleanup")
            return {
                "service": "duckdb",
                "deleted_count": 0,
                "errors": [],
                "success": True,
            }

        errors: List[str] = []
        total_deleted = 0

        try:
            # Count documents to delete
            count_query = f"""
            SELECT COUNT(*) as count
            FROM documents
            WHERE job_id = '{job_id}'
            """
            try:
                count_result = self.service.execute_query(count_query, limit=1)
                if count_result and "rows" in count_result:
                    docs_count = count_result["rows"][0][0] if count_result["rows"] else 0
                else:
                    docs_count = 0
            except Exception as exc:
                logger.warning(f"Failed to count documents for job {job_id}: {exc}")
                docs_count = 0

            # Count pages to delete
            pages_query = f"""
            SELECT COUNT(*) as count
            FROM pages
            WHERE job_id = '{job_id}'
            """
            try:
                pages_result = self.service.execute_query(pages_query, limit=1)
                if pages_result and "rows" in pages_result:
                    pages_count = pages_result["rows"][0][0] if pages_result["rows"] else 0
                else:
                    pages_count = 0
            except Exception as exc:
                logger.warning(f"Failed to count pages for job {job_id}: {exc}")
                pages_count = 0

            total_count = docs_count + pages_count

            if total_count == 0:
                logger.info(f"No records found for job {job_id} in DuckDB")
                return {
                    "service": "duckdb",
                    "deleted_count": 0,
                    "errors": [],
                    "success": True,
                }

            # Delete from pages table first (has foreign key to documents)
            if pages_count > 0:
                delete_pages_query = f"""
                DELETE FROM pages
                WHERE job_id = '{job_id}'
                """
                try:
                    self.service.execute_query(delete_pages_query, limit=None)
                    total_deleted += pages_count
                    logger.info(f"Deleted {pages_count} pages for job {job_id}")
                except Exception as exc:
                    error_msg = f"Failed to delete pages: {exc}"
                    logger.exception(error_msg)
                    errors.append(error_msg)

            # Delete from documents table
            if docs_count > 0:
                delete_docs_query = f"""
                DELETE FROM documents
                WHERE job_id = '{job_id}'
                """
                try:
                    self.service.execute_query(delete_docs_query, limit=None)
                    total_deleted += docs_count
                    logger.info(f"Deleted {docs_count} documents for job {job_id}")
                except Exception as exc:
                    error_msg = f"Failed to delete documents: {exc}"
                    logger.exception(error_msg)
                    errors.append(error_msg)

        except Exception as exc:
            error_msg = f"Unexpected error during cleanup: {exc}"
            logger.exception(error_msg)
            errors.append(error_msg)
            return {
                "service": "duckdb",
                "deleted_count": 0,
                "errors": errors,
                "success": False,
            }

        return {
            "service": "duckdb",
            "deleted_count": total_deleted,
            "errors": errors,
            "success": len(errors) == 0,
        }

    def get_job_data_count(self, job_id: str) -> int:
        """Get count of records associated with a job_id.

        Counts records from both documents and pages tables.

        Args:
            job_id: The job identifier to check

        Returns:
            Total number of records for this job
        """
        if not job_id:
            return 0

        if not self.service.is_enabled():
            return 0

        total_count = 0

        try:
            # Count documents
            docs_query = f"""
            SELECT COUNT(*) as count
            FROM documents
            WHERE job_id = '{job_id}'
            """
            try:
                result = self.service.execute_query(docs_query, limit=1)
                if result and "rows" in result:
                    total_count += result["rows"][0][0] if result["rows"] else 0
            except Exception as exc:
                logger.warning(f"Failed to count documents: {exc}")

            # Count pages
            pages_query = f"""
            SELECT COUNT(*) as count
            FROM pages
            WHERE job_id = '{job_id}'
            """
            try:
                result = self.service.execute_query(pages_query, limit=1)
                if result and "rows" in result:
                    total_count += result["rows"][0][0] if result["rows"] else 0
            except Exception as exc:
                logger.warning(f"Failed to count pages: {exc}")

        except Exception as exc:
            logger.warning(f"Failed to count records for job {job_id}: {exc}")
            return 0

        return total_count
