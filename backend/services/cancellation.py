"""Service cancellation notification system.

This module provides a mechanism to notify external services (ColPali, OCR, MinIO, Qdrant)
when a job is cancelled, allowing them to abort ongoing work.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class ServiceCancellationNotifier:
    """Notifies external services when jobs are cancelled."""

    def __init__(
        self,
        colpali_service=None,
        ocr_service=None,
        minio_service=None,
        qdrant_service=None,
    ):
        """Initialize with service instances.

        Args:
            colpali_service: ColPali embedding service
            ocr_service: OCR processing service
            minio_service: MinIO storage service
            qdrant_service: Qdrant vector database service
        """
        self.colpali_service = colpali_service
        self.ocr_service = ocr_service
        self.minio_service = minio_service
        self.qdrant_service = qdrant_service

    def notify_cancellation(self, job_id: str) -> dict[str, bool]:
        """Notify all services that a job has been cancelled.

        Args:
            job_id: The job ID to cancel

        Returns:
            Dict mapping service name to success status
        """
        results = {}

        # Notify ColPali
        if self.colpali_service:
            results["colpali"] = self._notify_colpali(job_id)

        # Notify OCR service
        if self.ocr_service:
            results["ocr"] = self._notify_ocr(job_id)

        # Notify MinIO
        if self.minio_service:
            results["minio"] = self._notify_minio(job_id)

        # Notify Qdrant
        if self.qdrant_service:
            results["qdrant"] = self._notify_qdrant(job_id)

        # Log results
        successful = sum(1 for success in results.values() if success)
        logger.info(
            f"Cancellation notification for job {job_id}: "
            f"{successful}/{len(results)} services notified successfully",
            extra={"job_id": job_id, "results": results},
        )

        return results

    def _notify_colpali(self, job_id: str) -> bool:
        """Notify ColPali service of cancellation."""
        if not hasattr(self.colpali_service, "cancel_job"):
            logger.debug("ColPali service does not support cancellation API")
            return False

        try:
            self.colpali_service.cancel_job(job_id)
            logger.info(f"ColPali cancellation sent for job {job_id}")
            return True
        except Exception as exc:
            logger.warning(f"Failed to notify ColPali of cancellation: {exc}")
            return False

    def _notify_ocr(self, job_id: str) -> bool:
        """Notify OCR service of cancellation."""
        if not hasattr(self.ocr_service, "cancel_job"):
            logger.debug("OCR service does not support cancellation API")
            return False

        try:
            self.ocr_service.cancel_job(job_id)
            logger.info(f"OCR cancellation sent for job {job_id}")
            return True
        except Exception as exc:
            logger.warning(f"Failed to notify OCR of cancellation: {exc}")
            return False

    def _notify_minio(self, job_id: str) -> bool:
        """Notify MinIO service of cancellation."""
        if not hasattr(self.minio_service, "cancel_job"):
            logger.debug("MinIO service does not support cancellation API")
            return False

        try:
            self.minio_service.cancel_job(job_id)
            logger.info(f"MinIO cancellation sent for job {job_id}")
            return True
        except Exception as exc:
            logger.warning(f"Failed to notify MinIO of cancellation: {exc}")
            return False

    def _notify_qdrant(self, job_id: str) -> bool:
        """Notify Qdrant service of cancellation."""
        if not hasattr(self.qdrant_service, "cancel_job"):
            logger.debug("Qdrant service does not support cancellation API")
            return False

        try:
            self.qdrant_service.cancel_job(job_id)
            logger.info(f"Qdrant cancellation sent for job {job_id}")
            return True
        except Exception as exc:
            logger.warning(f"Failed to notify Qdrant of cancellation: {exc}")
            return False


# Global notifier instance (initialized by app startup)
_notifier: Optional[ServiceCancellationNotifier] = None


def initialize_notifier(
    colpali_service=None,
    ocr_service=None,
    minio_service=None,
    qdrant_service=None,
) -> None:
    """Initialize the global service cancellation notifier.

    Called during application startup.
    """
    global _notifier
    _notifier = ServiceCancellationNotifier(
        colpali_service=colpali_service,
        ocr_service=ocr_service,
        minio_service=minio_service,
        qdrant_service=qdrant_service,
    )
    logger.info("Service cancellation notifier initialized")


def notify_job_cancellation(job_id: str) -> dict[str, bool]:
    """Notify all services that a job has been cancelled.

    Args:
        job_id: The job ID to cancel

    Returns:
        Dict mapping service name to success status
    """
    if _notifier is None:
        logger.warning("Service cancellation notifier not initialized")
        return {}

    return _notifier.notify_cancellation(job_id)


def get_notifier() -> Optional[ServiceCancellationNotifier]:
    """Get the global notifier instance."""
    return _notifier
