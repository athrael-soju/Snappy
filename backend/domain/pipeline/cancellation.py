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

    def _wait_for_service_restart(
        self, service_name: str, health_check_fn, timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Wait for a service to restart by polling its health check.

        Args:
            service_name: Name of the service (for logging)
            health_check_fn: Function to call for health check
            timeout: Maximum seconds to wait for restart

        Returns:
            Dictionary with restart verification results
        """
        import time

        start_time = time.time()
        check_interval = 0.5  # Check every 500ms

        # Phase 1: Wait for service to go down (max 5 seconds)
        logger.info(f"Waiting for {service_name} to go down...")
        down_detected = False
        while time.time() - start_time < 5:
            try:
                if not health_check_fn():
                    down_detected = True
                    logger.info(f"{service_name} is down")
                    break
            except Exception:
                down_detected = True
                logger.info(f"{service_name} is down")
                break
            time.sleep(check_interval)

        if not down_detected:
            logger.warning(f"{service_name} did not go down within 5 seconds")

        # Phase 2: Wait for service to come back up
        logger.info(f"Waiting for {service_name} to come back up...")
        restart_time = time.time()
        while time.time() - start_time < timeout:
            try:
                if health_check_fn():
                    elapsed = time.time() - start_time
                    logger.info(f"{service_name} is back up (took {elapsed:.1f}s)")
                    return {
                        "success": True,
                        "message": f"Restarted successfully in {elapsed:.1f}s",
                        "elapsed_seconds": round(elapsed, 1),
                    }
            except Exception as e:
                pass  # Service still down, keep waiting
            time.sleep(check_interval)

        # Timeout reached
        elapsed = time.time() - start_time
        logger.error(f"{service_name} did not come back up within {timeout}s")
        return {
            "success": False,
            "message": f"Restart timeout after {elapsed:.1f}s",
            "elapsed_seconds": round(elapsed, 1),
        }

    def restart_services(
        self,
        job_id: str,
        wait_for_restart: bool = True,
        timeout: int = 30,
        progress_callback=None,
    ) -> Dict[str, Any]:
        """
        Restart ColPali and DeepSeek OCR services to stop any ongoing processing.

        This method sends restart requests to both services. The services will:
        1. Immediately stop any ongoing batch processing
        2. Exit the process cleanly
        3. Automatically restart via Docker's restart policy
        4. (Optional) Wait for services to come back up

        Args:
            job_id: Job identifier (for logging purposes)
            wait_for_restart: If True, wait for services to restart before returning
            timeout: Maximum seconds to wait for each service to restart
            progress_callback: Optional callback(percent, message) for progress updates

        Returns:
            Dictionary containing restart results for each service
        """
        logger.info(
            f"RESTART SERVICES: job_id={job_id}, wait={wait_for_restart}",
            extra={"job_id": job_id},
        )

        results = {
            "colpali": {"success": False, "message": "Not attempted"},
            "deepseek_ocr": {"success": False, "message": "Not attempted"},
        }

        # Restart ColPali service (25-50%)
        if self.colpali_client:
            try:
                if progress_callback:
                    progress_callback(25, "Restarting ColPali service...")

                success = self.colpali_client.restart()
                if success:
                    logger.info("ColPali service restart requested successfully")
                    if wait_for_restart:
                        results["colpali"] = self._wait_for_service_restart(
                            "ColPali", self.colpali_client.health_check, timeout
                        )
                        if progress_callback:
                            progress_callback(50, "ColPali service restarted")
                    else:
                        results["colpali"] = {
                            "success": True,
                            "message": "Restart requested (not waiting)",
                        }
                else:
                    logger.warning("ColPali service restart request failed")
                    results["colpali"] = {
                        "success": False,
                        "message": "Restart request failed",
                    }
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

        # Restart DeepSeek OCR service (50-75%)
        if self.ocr_client:
            try:
                if progress_callback:
                    progress_callback(50, "Restarting DeepSeek OCR service...")

                success = self.ocr_client.restart()
                if success:
                    logger.info("DeepSeek OCR service restart requested successfully")
                    if wait_for_restart:
                        results["deepseek_ocr"] = self._wait_for_service_restart(
                            "DeepSeek OCR", self.ocr_client.health_check, timeout
                        )
                        if progress_callback:
                            progress_callback(75, "DeepSeek OCR service restarted")
                    else:
                        results["deepseek_ocr"] = {
                            "success": True,
                            "message": "Restart requested (not waiting)",
                        }
                else:
                    logger.warning("DeepSeek OCR service restart request failed")
                    results["deepseek_ocr"] = {
                        "success": False,
                        "message": "Restart request failed",
                    }
            except Exception as e:
                logger.error(
                    f"Error requesting DeepSeek OCR restart: {e}", exc_info=True
                )
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
        progress_callback=None,
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
            progress_callback: Optional callback(percent, message) for progress updates

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

        # 0. Restart services to stop any ongoing processing (25-75%)
        if restart_services:
            results["restart_results"] = self.restart_services(
                job_id, progress_callback=progress_callback
            )

        if not filename:
            logger.warning(
                f"No filename provided for job {job_id}, skipping service cleanup"
            )
            results["errors"].append(
                "No filename provided - cannot cleanup service data"
            )
            results["overall_success"] = False
            return results

        # 1. Cleanup Qdrant vector points (75-81%)
        if progress_callback:
            progress_callback(75, "Cleaning up vector database...")
        results["cleanup_results"]["qdrant"] = self._cleanup_qdrant(
            filename=filename,
            collection_name=collection_name or config.QDRANT_COLLECTION_NAME,
        )
        if progress_callback:
            progress_callback(81, "Vector database cleaned")

        # 2. Cleanup MinIO objects (81-87%)
        if progress_callback:
            progress_callback(81, "Cleaning up object storage...")
        results["cleanup_results"]["minio"] = self._cleanup_minio(filename=filename)
        if progress_callback:
            progress_callback(87, "Object storage cleaned")

        # 3. Cleanup DuckDB records (87-93%)
        if progress_callback:
            progress_callback(87, "Cleaning up metadata database...")
        results["cleanup_results"]["duckdb"] = self._cleanup_duckdb(filename=filename)
        if progress_callback:
            progress_callback(93, "Metadata database cleaned")

        # 4. Cleanup temporary files (93-100%)
        if progress_callback:
            progress_callback(93, "Cleaning up temporary files...")
        results["cleanup_results"]["temp_files"] = self._cleanup_temp_files(
            job_id=job_id, filename=filename
        )
        if progress_callback:
            progress_callback(100, "Cleanup completed")

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

            # Skip jobs without a valid job_id to avoid passing None to cleanup_job_data
            if not job_id:
                logger.warning("Skipping job with missing job_id")
                raise ValueError("job_id is required for cleanup")
            else:
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
