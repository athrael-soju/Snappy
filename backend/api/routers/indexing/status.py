from __future__ import annotations

import asyncio
import json
import logging

from api.progress import progress_manager
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["indexing"])


@router.post("/index/cancel/{job_id}")
async def cancel_upload(job_id: str):
    """Cancel an ongoing upload/indexing job."""
    logger.info(
        "Job cancellation requested",
        extra={"operation": "cancel_upload", "job_id": job_id},
    )

    success = progress_manager.cancel(job_id)
    if success:
        logger.info(
            "Job cancelled successfully",
            extra={"operation": "cancel_upload", "job_id": job_id},
        )
        return {
            "status": "cancelled",
            "job_id": job_id,
            "message": "Upload cancelled successfully",
        }

    job_data = progress_manager.get(job_id)
    if not job_data:
        logger.warning(
            "Job cancellation failed: job not found",
            extra={"operation": "cancel_upload", "job_id": job_id},
        )
        raise HTTPException(status_code=404, detail="Job not found")

    logger.warning(
        "Job cancellation failed: invalid status",
        extra={
            "operation": "cancel_upload",
            "job_id": job_id,
            "current_status": job_data.get("status"),
        },
    )
    raise HTTPException(
        status_code=400,
        detail=f"Cannot cancel job in status: {job_data.get('status')}",
    )


@router.get("/progress/stream/{job_id}")
async def stream_progress(job_id: str):
    logger.debug(
        "Progress stream opened",
        extra={"operation": "stream_progress", "job_id": job_id},
    )

    async def event_stream():
        last_current = None
        last_status = None
        while True:
            data = progress_manager.get(job_id)
            if not data:
                logger.warning(
                    "Progress stream ended: job not found",
                    extra={"operation": "stream_progress", "job_id": job_id},
                )
                yield f"event: not_found\n" + f"data: {json.dumps({'job_id': job_id})}\n\n"
                return

            total = max(1, int(data.get("total") or 0))
            try:
                pct = (
                    int(round(((int(data.get("current") or 0) / total) * 100)))
                    if data.get("total")
                    else 0
                )
            except Exception:
                pct = 0

            payload = {
                "job_id": data.get("job_id"),
                "status": data.get("status"),
                "current": int(data.get("current") or 0),
                "total": int(data.get("total") or 0),
                "percent": pct,
                "message": data.get("message"),
                "error": data.get("error"),
                "details": data.get("details"),
            }

            changed = (
                payload["current"] != (last_current if last_current is not None else -1)
            ) or (payload["status"] != last_status)
            if changed:
                yield "event: progress\n" + f"data: {json.dumps(payload)}\n\n"
                last_current = payload["current"]
                last_status = payload["status"]
            else:
                yield "event: heartbeat\n" + "data: {}\n\n"

            if payload["status"] in ("completed", "failed", "cancelled"):
                logger.info(
                    "Progress stream ended",
                    extra={
                        "operation": "stream_progress",
                        "job_id": job_id,
                        "final_status": payload["status"],
                        "total": payload["total"],
                        "completed": payload["current"],
                    },
                )
                return

            await asyncio.sleep(1.0)

    return StreamingResponse(event_stream(), media_type="text/event-stream")


__all__ = ["cancel_upload", "stream_progress"]
