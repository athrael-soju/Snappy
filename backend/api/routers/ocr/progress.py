from __future__ import annotations

import asyncio
import json
import logging

from api.progress import progress_manager
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["ocr"])


@router.get("/progress/{job_id}")
async def get_progress(job_id: str):
    """Get OCR processing progress for a job."""
    logger.debug(
        "OCR progress requested", extra={"operation": "get_progress", "job_id": job_id}
    )

    job = progress_manager.get(job_id)
    if not job:
        logger.warning(
            "OCR progress: job not found",
            extra={"operation": "get_progress", "job_id": job_id},
        )
        raise HTTPException(404, f"Job not found: {job_id}")

    return job


@router.get("/progress/stream/{job_id}")
async def stream_progress(job_id: str):
    """Stream OCR processing progress via Server-Sent Events."""
    logger.debug(
        "OCR progress stream opened",
        extra={"operation": "stream_progress", "job_id": job_id},
    )

    async def event_generator():
        while True:
            job = progress_manager.get(job_id)
            if not job:
                logger.warning(
                    "OCR progress stream: job not found",
                    extra={"operation": "stream_progress", "job_id": job_id},
                )
                yield "data: " + json.dumps({"error": "Job not found"}) + "\n\n"
                break

            yield "data: " + json.dumps(job) + "\n\n"

            if job["status"] in ("completed", "failed", "cancelled"):
                logger.info(
                    "OCR progress stream ended",
                    extra={
                        "operation": "stream_progress",
                        "job_id": job_id,
                        "final_status": job["status"],
                    },
                )
                break

            await asyncio.sleep(0.5)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/cancel/{job_id}")
async def cancel_job(job_id: str):
    """Cancel a running OCR job."""
    logger.info(
        "OCR job cancellation requested",
        extra={"operation": "cancel_job", "job_id": job_id},
    )

    cancelled = progress_manager.cancel(job_id)
    if not cancelled:
        logger.warning(
            "OCR job cancellation failed",
            extra={"operation": "cancel_job", "job_id": job_id},
        )
        raise HTTPException(400, f"Job cannot be cancelled: {job_id}")

    logger.info(
        "OCR job cancelled successfully",
        extra={"operation": "cancel_job", "job_id": job_id},
    )
    return {"status": "cancelled", "job_id": job_id}


__all__ = ["cancel_job", "get_progress", "stream_progress"]
