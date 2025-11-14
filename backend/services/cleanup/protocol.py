"""Protocol for cleanup services."""

from typing import Dict, Protocol, runtime_checkable


@runtime_checkable
class CleanupService(Protocol):
    """Protocol for services that can clean up data by job_id.

    All storage services (Qdrant, MinIO, DuckDB) should implement this protocol
    to enable centralized cleanup coordination when jobs are cancelled or fail.
    """

    def cleanup_by_job_id(self, job_id: str) -> Dict[str, any]:
        """Remove all data associated with a job_id.

        Args:
            job_id: The job identifier to clean up

        Returns:
            Dict with cleanup statistics:
            {
                "service": str,  # Service name
                "deleted_count": int,  # Number of items deleted
                "errors": List[str],  # Any errors encountered
                "success": bool  # Overall success status
            }
        """
        ...

    def get_job_data_count(self, job_id: str) -> int:
        """Get count of data items associated with a job_id.

        Args:
            job_id: The job identifier to check

        Returns:
            Number of data items (points, objects, records) for this job
        """
        ...
