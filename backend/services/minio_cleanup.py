"""MinIO cleanup operations for job cancellation."""

import logging
from typing import Dict, List

from minio import Minio
from minio.deleteobjects import DeleteObject

logger = logging.getLogger(__name__)


class MinioCleanupService:
    """Service for cleaning up MinIO data by job_id.

    Implements the CleanupService protocol for MinIO storage.

    Note: MinIO doesn't support filtering by metadata/tags in list operations,
    so we need to list all objects and filter by tags. For better performance,
    we track job_id in object metadata/tags during upload.
    """

    def __init__(self, minio_service: Minio, bucket_name: str):
        """Initialize MinIO cleanup service.

        Args:
            minio_service: MinIO client instance
            bucket_name: Name of the bucket to clean up
        """
        self.service = minio_service
        self.bucket_name = bucket_name

    def cleanup_by_job_id(self, job_id: str) -> Dict[str, any]:
        """Remove all objects associated with a job_id.

        This method lists all objects in the bucket and filters by job_id tag.
        For large buckets, this may be slow. Consider implementing prefix-based
        cleanup if job_id is included in object paths.

        Args:
            job_id: The job identifier to clean up

        Returns:
            Dict with cleanup statistics
        """
        if not job_id:
            return {
                "service": "minio",
                "deleted_count": 0,
                "errors": ["Empty job_id provided"],
                "success": False,
            }

        errors: List[str] = []
        deleted_count = 0
        objects_to_delete: List[str] = []

        try:
            # Check if bucket exists
            if not self.service.bucket_exists(self.bucket_name):
                logger.info(
                    f"Bucket {self.bucket_name} does not exist, nothing to clean up"
                )
                return {
                    "service": "minio",
                    "deleted_count": 0,
                    "errors": [],
                    "success": True,
                }

            # List all objects and filter by job_id tag
            # Note: This approach lists all objects and checks tags individually
            # For better performance, consider using object path prefixes with job_id
            try:
                objects = self.service.list_objects(
                    self.bucket_name, recursive=True
                )

                for obj in objects:
                    try:
                        # Get object tags to check for job_id
                        tags = self.service.get_object_tags(
                            self.bucket_name, obj.object_name
                        )

                        # Check if job_id tag matches
                        if tags and tags.get("job_id") == job_id:
                            objects_to_delete.append(obj.object_name)

                    except Exception as exc:
                        # Object might not have tags, skip it
                        logger.debug(
                            f"Could not get tags for {obj.object_name}: {exc}"
                        )
                        continue

            except Exception as exc:
                error_msg = f"Failed to list objects: {exc}"
                logger.exception(error_msg)
                errors.append(error_msg)
                return {
                    "service": "minio",
                    "deleted_count": 0,
                    "errors": errors,
                    "success": False,
                }

            # Delete objects if any found
            if objects_to_delete:
                try:
                    delete_objects = [
                        DeleteObject(name) for name in objects_to_delete
                    ]
                    delete_errors = self.service.remove_objects(
                        self.bucket_name, delete_objects
                    )

                    # Count deletion errors
                    error_count = 0
                    for error in delete_errors:
                        error_count += 1
                        errors.append(f"Failed to delete {error.object_name}: {error}")

                    deleted_count = len(objects_to_delete) - error_count

                    if deleted_count > 0:
                        logger.info(
                            f"Deleted {deleted_count} objects for job {job_id} from MinIO"
                        )
                    if error_count > 0:
                        logger.warning(
                            f"Failed to delete {error_count} objects for job {job_id}"
                        )

                except Exception as exc:
                    error_msg = f"Failed to delete objects: {exc}"
                    logger.exception(error_msg)
                    errors.append(error_msg)
                    return {
                        "service": "minio",
                        "deleted_count": 0,
                        "errors": errors,
                        "success": False,
                    }
            else:
                logger.info(f"No objects found for job {job_id} in MinIO")

        except Exception as exc:
            error_msg = f"Unexpected error during cleanup: {exc}"
            logger.exception(error_msg)
            errors.append(error_msg)
            return {
                "service": "minio",
                "deleted_count": 0,
                "errors": errors,
                "success": False,
            }

        return {
            "service": "minio",
            "deleted_count": deleted_count,
            "errors": errors,
            "success": len(errors) == 0,
        }

    def get_job_data_count(self, job_id: str) -> int:
        """Get count of objects associated with a job_id.

        Args:
            job_id: The job identifier to check

        Returns:
            Number of objects for this job
        """
        if not job_id:
            return 0

        count = 0

        try:
            # Check if bucket exists
            if not self.service.bucket_exists(self.bucket_name):
                return 0

            # List all objects and count those with matching job_id tag
            objects = self.service.list_objects(self.bucket_name, recursive=True)

            for obj in objects:
                try:
                    tags = self.service.get_object_tags(
                        self.bucket_name, obj.object_name
                    )
                    if tags and tags.get("job_id") == job_id:
                        count += 1
                except Exception:
                    # Skip objects without tags
                    continue

        except Exception as exc:
            logger.warning(f"Failed to count objects for job {job_id}: {exc}")
            return 0

        return count
