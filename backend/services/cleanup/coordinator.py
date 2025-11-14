"""Centralized cleanup coordinator for job cancellation."""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional

from .protocol import CleanupService

logger = logging.getLogger(__name__)


class CleanupCoordinator:
    """Coordinates cleanup across multiple storage services.

    This coordinator manages the cleanup of partial/failed job data across
    Qdrant, MinIO, and DuckDB when jobs are cancelled or fail.

    Design principles:
    - Parallel cleanup across services for speed
    - Continue on error (attempt cleanup on all services even if one fails)
    - Detailed reporting of cleanup results
    - Thread-safe operation
    """

    def __init__(
        self,
        qdrant_cleanup: Optional[CleanupService] = None,
        minio_cleanup: Optional[CleanupService] = None,
        duckdb_cleanup: Optional[CleanupService] = None,
    ):
        """Initialize cleanup coordinator.

        Args:
            qdrant_cleanup: Qdrant cleanup service
            minio_cleanup: MinIO cleanup service
            duckdb_cleanup: DuckDB cleanup service
        """
        self.services: Dict[str, CleanupService] = {}

        if qdrant_cleanup is not None:
            self.services["qdrant"] = qdrant_cleanup
        if minio_cleanup is not None:
            self.services["minio"] = minio_cleanup
        if duckdb_cleanup is not None:
            self.services["duckdb"] = duckdb_cleanup

        logger.info(
            f"CleanupCoordinator initialized with services: {list(self.services.keys())}"
        )

    def cleanup_job(self, job_id: str) -> Dict[str, any]:
        """Clean up all data associated with a job across all services.

        This method runs cleanup in parallel across all registered services
        and aggregates the results.

        Args:
            job_id: The job identifier to clean up

        Returns:
            Dict with aggregated cleanup results:
            {
                "job_id": str,
                "total_deleted": int,
                "services": {
                    "qdrant": {...},
                    "minio": {...},
                    "duckdb": {...}
                },
                "errors": List[str],
                "success": bool
            }
        """
        if not job_id:
            logger.warning("cleanup_job called with empty job_id")
            return {
                "job_id": job_id,
                "total_deleted": 0,
                "services": {},
                "errors": ["Empty job_id provided"],
                "success": False,
            }

        if not self.services:
            logger.warning("No cleanup services registered")
            return {
                "job_id": job_id,
                "total_deleted": 0,
                "services": {},
                "errors": ["No cleanup services available"],
                "success": False,
            }

        logger.info(f"Starting cleanup for job {job_id}")

        results = {}
        errors: List[str] = []
        total_deleted = 0

        # Execute cleanup in parallel across all services
        with ThreadPoolExecutor(max_workers=len(self.services)) as executor:
            future_to_service = {
                executor.submit(service.cleanup_by_job_id, job_id): name
                for name, service in self.services.items()
            }

            for future in as_completed(future_to_service):
                service_name = future_to_service[future]
                try:
                    result = future.result()
                    results[service_name] = result

                    # Aggregate statistics
                    deleted = result.get("deleted_count", 0)
                    total_deleted += deleted

                    # Collect errors
                    service_errors = result.get("errors", [])
                    if service_errors:
                        errors.extend(
                            [f"{service_name}: {err}" for err in service_errors]
                        )

                    logger.info(
                        f"Cleanup for {service_name} completed: {deleted} items deleted"
                    )

                except Exception as exc:
                    error_msg = f"Cleanup failed for {service_name}: {exc}"
                    logger.exception(error_msg)
                    errors.append(error_msg)
                    results[service_name] = {
                        "service": service_name,
                        "deleted_count": 0,
                        "errors": [str(exc)],
                        "success": False,
                    }

        # Determine overall success (at least one service succeeded without errors)
        success = any(r.get("success", False) for r in results.values())

        cleanup_result = {
            "job_id": job_id,
            "total_deleted": total_deleted,
            "services": results,
            "errors": errors,
            "success": success,
        }

        if success:
            logger.info(
                f"Cleanup for job {job_id} completed: {total_deleted} total items deleted"
            )
        else:
            logger.warning(
                f"Cleanup for job {job_id} completed with errors: {len(errors)} errors"
            )

        return cleanup_result

    def get_job_data_summary(self, job_id: str) -> Dict[str, any]:
        """Get summary of data associated with a job across all services.

        Args:
            job_id: The job identifier to check

        Returns:
            Dict with data counts per service:
            {
                "job_id": str,
                "services": {
                    "qdrant": int,
                    "minio": int,
                    "duckdb": int
                },
                "total_items": int
            }
        """
        if not job_id:
            return {"job_id": job_id, "services": {}, "total_items": 0}

        counts = {}
        total = 0

        for name, service in self.services.items():
            try:
                count = service.get_job_data_count(job_id)
                counts[name] = count
                total += count
            except Exception as exc:
                logger.warning(f"Failed to get count from {name}: {exc}")
                counts[name] = 0

        return {"job_id": job_id, "services": counts, "total_items": total}
