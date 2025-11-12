from __future__ import annotations

import asyncio
import json

from api.progress import progress_manager
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="", tags=["ocr"])


@router.get("/progress/{job_id}")
async def get_progress(job_id: str):
    """Get OCR processing progress for a job."""
    job = progress_manager.get(job_id)
    if not job:
        raise HTTPException(404, f"Job not found: {job_id}")
    return job


@router.get("/progress/stream/{job_id}")
async def stream_progress(job_id: str):
    """Stream OCR processing progress via Server-Sent Events."""

    async def event_generator():
        while True:
            job = progress_manager.get(job_id)
            if not job:
                yield "data: " + json.dumps({"error": "Job not found"}) + "\n\n"
                break

            yield "data: " + json.dumps(job) + "\n\n"

            if job["status"] in ("completed", "failed", "cancelled"):
                break

            await asyncio.sleep(0.5)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/cancel/{job_id}")
async def cancel_job(job_id: str):
    """Cancel a running OCR job."""
    cancelled = progress_manager.cancel(job_id)
    if not cancelled:
        raise HTTPException(400, f"Job cannot be cancelled: {job_id}")
    return {"status": "cancelled", "job_id": job_id}


__all__ = ["cancel_job", "get_progress", "stream_progress"]
