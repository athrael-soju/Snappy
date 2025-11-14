"""
Cancellation Service - Coordinates cleanup across all services when a job is cancelled or fails.

This service implements the separation of concerns pattern by:
1. Managing job-level cancellation coordination
2. Delegating service-specific cleanup to respective services
3. Tracking cleanup results for audit/debugging
"""

import logging
from typing import Dict, Any, Optional, TYPE_CHECKING
from pathlib import Path
import shutil

from clients.minio import MinioClient
from clients.duckdb import DuckDBClient
from clients.qdrant.collection import CollectionManager
import config

if TYPE_CHECKING:
    from clients.colpali import ColPaliClient
    from clients.ocr.client import OcrClient

logger = logging.getLogger(__name__)


class CancellationService:
    """
    Centralized service for managing job cancellations and cleanup operations.

    Responsibilities:
    - Coordinate cleanup across Qdrant, MinIO, and DuckDB
    - Remove temporary files associated with cancelled jobs
    - Provide detailed cleanup reports for monitoring
    - Handle partial cleanup failures gracefully
    """

    def __init__(
        self,
        minio_service: Optional[MinioClient] = None,
        duckdb_service: Optional[DuckDBClient] = None,
        qdrant_collection_manager: Optional[CollectionManager] = None,
        colpali_client: Optional["ColPaliClient"] = None,
        ocr_client: Optional["OcrClient"] = None,
    ):
        """
        Initialize the cancellation service with dependent services.

        Args:
            minio_service: MinIO service instance for object storage cleanup
            duckdb_service: DuckDB service instance for database cleanup
            qdrant_collection_manager: Qdrant collection manager for vector database cleanup
            colpali_client: ColPali client instance for service restart
            ocr_client: OCR client instance for service restart
        """
        self.minio_service = minio_service or MinioClient()
        self.duckdb_service = duckdb_service or DuckDBClient()
        self.qdrant_collection_manager = (
            qdrant_collection_manager or CollectionManager()
        )
        self.colpali_client = colpali_client
        self.ocr_client = ocr_client

    def restart_services(self, job_id: str) -> Dict[str, Any]:
        """
        Restart ColPali and DeepSeek OCR services to stop any ongoing processing.

        This method sends restart requests to both services. The services will:
        1. Immediately stop any ongoing batch processing
        2. Exit the process cleanly
        3. Automatically restart via Docker's restart policy

        This is a non-blocking operation - we send the restart request and continue.
        The services will restart in the background.

        Args:
            job_id: Job identifier (for logging purposes)

        Returns:
            Dictionary containing restart results for each service
        """
        logger.info(
            f"RESTART SERVICES: job_id={job_id}",
            extra={"job_id": job_id},
        )

        results = {
            "colpali": {"success": False, "message": "Not attempted"},
            "deepseek_ocr": {"success": False, "message": "Not attempted"},
        }

        # Restart ColPali service
        if self.colpali_client:
            try:
                success = self.colpali_client.restart()
                results["colpali"] = {
                    "success": success,
                    "message": "Restart requested" if success else "Restart failed",
                }
                if success:
                    logger.info("ColPali service restart requested successfully")
                else:
                    logger.warning("ColPali service restart request failed")
            except Exception as e:
                logger.error(f"Error requesting ColPali restart: {e}", exc_info=True)
                results["colpali"] = {
                    "success": False,
                    "message": f"Error: {str(e)}",
                }
        else:
            logger.debug("ColPali client not available, skipping restart")
            results["colpali"] = {
                "success": False,
                "message": "Client not available",
            }

        # Restart DeepSeek OCR service
        if self.ocr_client:
            try:
                success = self.ocr_client.restart()
                results["deepseek_ocr"] = {
                    "success": success,
                    "message": "Restart requested" if success else "Restart failed",
                }
                if success:
                    logger.info("DeepSeek OCR service restart requested successfully")
                else:
                    logger.warning("DeepSeek OCR service restart request failed")
            except Exception as e:
                logger.error(f"Error requesting DeepSeek OCR restart: {e}", exc_info=True)
                results["deepseek_ocr"] = {
                    "success": False,
                    "message": f"Error: {str(e)}",
                }
        else:
            logger.debug("DeepSeek OCR client not available, skipping restart")
            results["deepseek_ocr"] = {
                "success": False,
                "message": "Client not available",
            }

        return results

    def cleanup_job_data(
        self,
        job_id: str,
        filename: Optional[str] = None,
        collection_name: Optional[str] = None,
        restart_services: bool = True,
    ) -> Dict[str, Any]:
        """
        Cleanup all data associated with a cancelled or failed job.

        This method coordinates cleanup across all services:
        0. (Optional) Restart ColPali and DeepSeek OCR services to stop ongoing processing
        1. Qdrant: Delete vector points for the document
        2. MinIO: Delete all objects under the document prefix
        3. DuckDB: Delete document and OCR records
        4. Filesystem: Remove temporary files

        Note: This is a synchronous blocking operation. All service calls are synchronous.

        Args:
            job_id: Unique identifier for the job
            filename: Document filename (used as identifier across services)
            collection_name: Qdrant collection name (defaults to config.QDRANT_COLLECTION_NAME)
            restart_services: Whether to restart ColPali and DeepSeek OCR services before cleanup

        Returns:
            Dictionary containing cleanup results for each service

        Example:
            {
                "job_id": "123e4567-e89b-12d3-a456-426614174000",
                "filename": "document.pdf",
                "restart_results": {
                    "colpali": {"success": true, "message": "Restart requested"},
                    "deepseek_ocr": {"success": true, "message": "Restart requested"}
                },
                "cleanup_results": {
                    "qdrant": {"success": true, "points_deleted": 15},
                    "minio": {"success": true, "objects_deleted": 45},
                    "duckdb": {"success": true, "records_deleted": 15},
                    "temp_files": {"success": true, "files_removed": 1}
                },
                "overall_success": true,
                "errors": []
            }
        """
        logger.info(
            f"CLEANUP STARTED: job_id={job_id}, filename={filename}, collection={collection_name}",
            extra={"job_id": job_id, "document_filename": filename},
        )

        results = {
            "job_id": job_id,
            "filename": filename,
            "restart_results": {},
            "cleanup_results": {},
            "overall_success": True,
            "errors": [],
        }

        # 0. Restart services to stop any ongoing processing
        if restart_services:
            results["restart_results"] = self.restart_services(job_id)

        if not filename:
            logger.warning(
                f"No filename provided for job {job_id}, skipping service cleanup"
            )
            results["errors"].append(
                "No filename provided - cannot cleanup service data"
            )
            results["overall_success"] = False
            return results

        # 1. Cleanup Qdrant vector points
        results["cleanup_results"]["qdrant"] = self._cleanup_qdrant(
            filename=filename,
            collection_name=collection_name or config.QDRANT_COLLECTION_NAME,
        )

        # 2. Cleanup MinIO objects
        results["cleanup_results"]["minio"] = self._cleanup_minio(filename=filename)

        # 3. Cleanup DuckDB records
        results["cleanup_results"]["duckdb"] = self._cleanup_duckdb(filename=filename)

        # 4. Cleanup temporary files
        results["cleanup_results"]["temp_files"] = self._cleanup_temp_files(
            job_id=job_id, filename=filename
        )

        # Aggregate results
        for service, result in results["cleanup_results"].items():
            if not result.get("success", False):
                results["overall_success"] = False
                if result.get("error"):
                    results["errors"].append(f"{service}: {result['error']}")

        if results["overall_success"]:
            logger.info(f"Successfully completed cleanup for job {job_id}")
        else:
            logger.warning(
                f"Cleanup completed with errors for job {job_id}: {results['errors']}"
            )

        return results

    def _cleanup_qdrant(self, filename: str, collection_name: str) -> Dict[str, Any]:
        """
        Delete all Qdrant points associated with a document.

        Args:
            filename: Document filename
            collection_name: Qdrant collection name

        Returns:
            Cleanup result dictionary
        """
        try:
            logger.debug(f"Cleaning up Qdrant points for filename={filename}")

            deleted_count = self.qdrant_collection_manager.delete_points_by_filename(
                filename=filename, collection_name=collection_name
            )

            return {
                "success": True,
                "points_deleted": deleted_count,
                "collection": collection_name,
            }

        except Exception as e:
            logger.error(f"Failed to cleanup Qdrant for {filename}: {e}", exc_info=True)
            return {"success": False, "points_deleted": 0, "error": str(e)}

    def _cleanup_minio(self, filename: str) -> Dict[str, Any]:
        """
        Delete all MinIO objects under the document prefix.

        MinIO structure: bucket/{filename}/page_number/...
        This deletes everything under {filename}/

        Args:
            filename: Document filename (used as prefix)

        Returns:
            Cleanup result dictionary
        """
        try:
            logger.debug(f"Cleaning up MinIO objects for filename={filename}")

            # Use clear_prefix to delete all objects under {filename}/
            prefix = f"{filename}/"
            result = self.minio_service.clear_prefix(prefix)

            deleted = result.get("deleted", 0)
            failed = result.get("failed", 0)

            return {
                "success": failed == 0,
                "objects_deleted": deleted,
                "objects_failed": failed,
                "prefix": prefix,
            }

        except Exception as e:
            logger.error(f"Failed to cleanup MinIO for {filename}: {e}", exc_info=True)
            return {"success": False, "objects_deleted": 0, "error": str(e)}

    def _cleanup_duckdb(self, filename: str) -> Dict[str, Any]:
        """
        Delete all DuckDB records associated with a document.

        Args:
            filename: Document filename

        Returns:
            Cleanup result dictionary
        """
        try:
            logger.debug(f"Cleaning up DuckDB records for filename={filename}")

            # delete_document returns a boolean
            success = self.duckdb_service.delete_document(filename)

            return {
                "success": success,
                "records_deleted": "unknown" if success else 0,
                "message": (
                    "Deleted document from DuckDB" if success else "Failed to delete"
                ),
            }

        except Exception as e:
            logger.error(f"Failed to cleanup DuckDB for {filename}: {e}", exc_info=True)
            return {"success": False, "records_deleted": 0, "error": str(e)}

    def _cleanup_temp_files(self, job_id: str, filename: str) -> Dict[str, Any]:
        """
        Remove temporary files created during job processing.

        Common temporary files:
        - Converted PDF files in temp directory
        - Intermediate processing files

        Args:
            job_id: Job identifier
            filename: Document filename

        Returns:
            Cleanup result dictionary
        """
        try:
            logger.debug(
                f"Cleaning up temporary files for job_id={job_id}, filename={filename}"
            )

            removed_files = []

            # Check for PDF conversion temp files
            # These are typically named {filename}.pdf or similar
            temp_dir = Path("/tmp")

            # Look for files matching the filename pattern
            if temp_dir.exists():
                for temp_file in temp_dir.glob(f"*{filename}*"):
                    try:
                        if temp_file.is_file():
                            temp_file.unlink()
                            removed_files.append(str(temp_file))
                            logger.debug(f"Removed temp file: {temp_file}")
                        elif temp_file.is_dir():
                            shutil.rmtree(temp_file)
                            removed_files.append(str(temp_file))
                            logger.debug(f"Removed temp directory: {temp_file}")
                    except Exception as e:
                        logger.warning(f"Failed to remove {temp_file}: {e}")

            return {
                "success": True,
                "files_removed": len(removed_files),
                "removed_paths": removed_files,
            }

        except Exception as e:
            logger.error(
                f"Failed to cleanup temp files for {filename}: {e}", exc_info=True
            )
            return {"success": False, "files_removed": 0, "error": str(e)}

    def cleanup_multiple_jobs(
        self, job_data: list[Dict[str, str]], collection_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Cleanup data for multiple jobs in batch.

        Useful for:
        - Bulk cancellation operations
        - System maintenance
        - Error recovery

        Args:
            job_data: List of job dictionaries with 'job_id' and 'filename' keys
            collection_name: Qdrant collection name

        Returns:
            Aggregated cleanup results
        """
        logger.info(f"Starting batch cleanup for {len(job_data)} jobs")

        results = {
            "total_jobs": len(job_data),
            "successful": 0,
            "failed": 0,
            "job_results": [],
        }

        for job in job_data:
            job_id = job.get("job_id")
            filename = job.get("filename")

            job_result = self.cleanup_job_data(
                job_id=job_id, filename=filename, collection_name=collection_name
            )

            results["job_results"].append(job_result)

            if job_result["overall_success"]:
                results["successful"] += 1
            else:
                results["failed"] += 1

        logger.info(
            f"Batch cleanup completed: {results['successful']} successful, "
            f"{results['failed']} failed"
        )

        return results


# Global instance for easy import
cancellation_service = CancellationService()
