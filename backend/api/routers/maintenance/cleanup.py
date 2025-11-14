"""Cleanup operations for job data removal."""

import logging
from typing import Dict

from api.dependencies import get_cleanup_coordinator
from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/cleanup/job/{job_id}")
async def cleanup_job_data(job_id: str) -> Dict:
    """Clean up all data associated with a specific job_id.

    This endpoint manually triggers cleanup of data across all services
    (Qdrant, MinIO, DuckDB) for a specific job. Useful for:
    - Cleaning up after failed jobs
    - Removing partial data from cancelled jobs
    - Manual cleanup operations

    Args:
        job_id: The job identifier to clean up

    Returns:
        Dict with cleanup statistics per service
    """
    if not job_id or not job_id.strip():
        raise HTTPException(status_code=400, detail="job_id is required")

    coordinator = get_cleanup_coordinator()
    if not coordinator:
        raise HTTPException(
            status_code=503,
            detail="Cleanup coordinator not available - services may not be initialized",
        )

    try:
        logger.info(f"Manual cleanup requested for job {job_id}")
        result = coordinator.cleanup_job(job_id)

        if not result.get("success"):
            logger.warning(
                f"Cleanup for job {job_id} completed with errors: {result.get('errors')}"
            )

        return {
            "job_id": job_id,
            "status": "completed" if result.get("success") else "completed_with_errors",
            "total_deleted": result.get("total_deleted", 0),
            "services": result.get("services", {}),
            "errors": result.get("errors", []),
        }

    except Exception as exc:
        logger.exception(f"Failed to clean up job {job_id}")
        raise HTTPException(
            status_code=500, detail=f"Cleanup failed: {str(exc)}"
        ) from exc


@router.get("/cleanup/job/{job_id}/info")
async def get_job_data_info(job_id: str) -> Dict:
    """Get information about data associated with a job_id.

    Returns counts of data items (points, objects, records) per service
    without performing any cleanup.

    Args:
        job_id: The job identifier to check

    Returns:
        Dict with data counts per service
    """
    if not job_id or not job_id.strip():
        raise HTTPException(status_code=400, detail="job_id is required")

    coordinator = get_cleanup_coordinator()
    if not coordinator:
        raise HTTPException(
            status_code=503,
            detail="Cleanup coordinator not available - services may not be initialized",
        )

    try:
        summary = coordinator.get_job_data_summary(job_id)
        return {
            "job_id": job_id,
            "services": summary.get("services", {}),
            "total_items": summary.get("total_items", 0),
        }

    except Exception as exc:
        logger.exception(f"Failed to get info for job {job_id}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get job info: {str(exc)}"
        ) from exc
