"""Qdrant cleanup operations for job cancellation."""

import logging
from typing import Dict, List

from qdrant_client import QdrantClient, models

logger = logging.getLogger(__name__)


class QdrantCleanupService:
    """Service for cleaning up Qdrant data by job_id.

    Implements the CleanupService protocol for Qdrant storage.
    """

    def __init__(self, qdrant_client: QdrantClient, collection_name: str):
        """Initialize Qdrant cleanup service.

        Args:
            qdrant_client: Qdrant client instance
            collection_name: Name of the collection to clean up
        """
        self.service = qdrant_client
        self.collection_name = collection_name

    def cleanup_by_job_id(self, job_id: str) -> Dict[str, any]:
        """Remove all points associated with a job_id.

        Args:
            job_id: The job identifier to clean up

        Returns:
            Dict with cleanup statistics
        """
        if not job_id:
            return {
                "service": "qdrant",
                "deleted_count": 0,
                "errors": ["Empty job_id provided"],
                "success": False,
            }

        errors: List[str] = []
        deleted_count = 0

        try:
            # Check if collection exists
            try:
                collections = self.service.get_collections()
                collection_exists = any(
                    c.name == self.collection_name for c in collections.collections
                )
            except Exception as exc:
                error_msg = f"Failed to check collection existence: {exc}"
                logger.warning(error_msg)
                return {
                    "service": "qdrant",
                    "deleted_count": 0,
                    "errors": [error_msg],
                    "success": False,
                }

            if not collection_exists:
                logger.info(
                    f"Collection {self.collection_name} does not exist, nothing to clean up"
                )
                return {
                    "service": "qdrant",
                    "deleted_count": 0,
                    "errors": [],
                    "success": True,
                }

            # First, count points with this job_id
            try:
                count_result = self.service.count(
                    collection_name=self.collection_name,
                    count_filter=models.Filter(
                        must=[
                            models.FieldCondition(
                                key="job_id",
                                match=models.MatchValue(value=job_id),
                            )
                        ]
                    ),
                )
                deleted_count = count_result.count
            except Exception as exc:
                logger.warning(f"Failed to count points for job {job_id}: {exc}")
                deleted_count = 0

            # Delete points with this job_id using filter
            if deleted_count > 0:
                try:
                    self.service.delete(
                        collection_name=self.collection_name,
                        points_selector=models.FilterSelector(
                            filter=models.Filter(
                                must=[
                                    models.FieldCondition(
                                        key="job_id",
                                        match=models.MatchValue(value=job_id),
                                    )
                                ]
                            )
                        ),
                    )
                    logger.info(
                        f"Deleted {deleted_count} points for job {job_id} from Qdrant"
                    )
                except Exception as exc:
                    error_msg = f"Failed to delete points: {exc}"
                    logger.exception(error_msg)
                    errors.append(error_msg)
                    return {
                        "service": "qdrant",
                        "deleted_count": 0,
                        "errors": errors,
                        "success": False,
                    }
            else:
                logger.info(f"No points found for job {job_id} in Qdrant")

        except Exception as exc:
            error_msg = f"Unexpected error during cleanup: {exc}"
            logger.exception(error_msg)
            errors.append(error_msg)
            return {
                "service": "qdrant",
                "deleted_count": 0,
                "errors": errors,
                "success": False,
            }

        return {
            "service": "qdrant",
            "deleted_count": deleted_count,
            "errors": errors,
            "success": len(errors) == 0,
        }

    def get_job_data_count(self, job_id: str) -> int:
        """Get count of points associated with a job_id.

        Args:
            job_id: The job identifier to check

        Returns:
            Number of points for this job
        """
        if not job_id:
            return 0

        try:
            # Check if collection exists
            try:
                collections = self.service.get_collections()
                collection_exists = any(
                    c.name == self.collection_name for c in collections.collections
                )
            except Exception:
                return 0

            if not collection_exists:
                return 0

            count_result = self.service.count(
                collection_name=self.collection_name,
                count_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="job_id",
                            match=models.MatchValue(value=job_id),
                        )
                    ]
                ),
            )
            return count_result.count

        except Exception as exc:
            logger.warning(f"Failed to count points for job {job_id}: {exc}")
            return 0
