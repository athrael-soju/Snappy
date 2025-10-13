import asyncio
import json
import logging
import os
import tempfile
import uuid
from typing import List

from api.dependencies import get_qdrant_service, qdrant_init_error
from api.progress import progress_manager
from api.utils import convert_pdf_paths_to_images
from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["indexing"])


UPLOAD_CHUNK_SIZE_BYTES = 4 * 1024 * 1024  # 4MB streaming chunks


@router.post("/index")
async def index(background_tasks: BackgroundTasks, files: List[UploadFile] = File(...)):
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    temp_paths: List[str] = []
    original_filenames: dict[str, str] = {}

    try:
        chunk_size = UPLOAD_CHUNK_SIZE_BYTES
        for upload in files:
            suffix = os.path.splitext(upload.filename or "")[1] or ".pdf"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                while True:
                    chunk = await upload.read(chunk_size)
                    if not chunk:
                        break
                    tmp.write(chunk)
                temp_paths.append(tmp.name)
                original_filenames[tmp.name] = upload.filename or "document.pdf"
            await upload.close()

        # Fail fast if dependencies are unavailable
        if not get_qdrant_service():
            raise HTTPException(
                status_code=503,
                detail=f"Service unavailable: {qdrant_init_error or 'Dependency services are down'}",
            )

        job_id = str(uuid.uuid4())
        progress_manager.create(job_id, total=0)
        progress_manager.start(job_id)

        class CancellationError(Exception):
            """Raised when a job is cancelled mid-flight."""

        def run_job(paths: List[str], filenames: dict[str, str]):
            try:
                if progress_manager.is_cancelled(job_id):
                    raise CancellationError("Job cancelled before processing started")

                progress_manager.update(
                    job_id, current=0, message="converting documents"
                )

                total_images, image_iterator = convert_pdf_paths_to_images(
                    paths, filenames
                )
                progress_manager.set_total(job_id, total_images)

                svc = get_qdrant_service()
                if not svc:
                    raise RuntimeError(
                        qdrant_init_error or "Dependency services are down"
                    )

                def progress_cb(current: int, info: dict | None = None):
                    if progress_manager.is_cancelled(job_id):
                        raise CancellationError("Job cancelled by user")

                    if info and info.get("stage") == "check_cancel":
                        return

                    message = None
                    if info and "stage" in info:
                        total_hint = info.get("total") or total_images
                        message = f"{info['stage']} {current}/{total_hint or '?'}"
                    progress_manager.update(job_id, current=current, message=message)

                progress_manager.update(job_id, current=0, message="indexing")
                msg = svc.index_documents(
                    image_iterator,
                    total_images=total_images,
                    progress_cb=progress_cb,
                )

                if progress_manager.is_cancelled(job_id):
                    raise CancellationError("Job cancelled after indexing")

                progress_manager.complete(job_id, message=msg)
            except CancellationError as exc:
                logger.info("Job %s cancelled: %s", job_id, exc)
            except Exception as exc:
                if not progress_manager.is_cancelled(job_id):
                    progress_manager.fail(job_id, error=str(exc))
                    logger.exception("Job %s failed", job_id)
            finally:
                for path in paths:
                    try:
                        os.unlink(path)
                    except Exception:
                        pass

        background_tasks.add_task(run_job, list(temp_paths), dict(original_filenames))
        return {"status": "started", "job_id": job_id, "total": 0}
    except Exception:
        for path in temp_paths:
            try:
                os.unlink(path)
            except Exception:
                pass
        raise


@router.post("/index/cancel/{job_id}")
async def cancel_upload(job_id: str):
    """Cancel an ongoing upload/indexing job."""
    success = progress_manager.cancel(job_id)
    if success:
        return {
            "status": "cancelled",
            "job_id": job_id,
            "message": "Upload cancelled successfully",
        }
    else:
        job_data = progress_manager.get(job_id)
        if not job_data:
            raise HTTPException(status_code=404, detail="Job not found")
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot cancel job in status: {job_data.get('status')}",
            )


@router.get("/progress/stream/{job_id}")
async def stream_progress(job_id: str):
    async def event_stream():
        last_current = None
        last_status = None
        while True:
            data = progress_manager.get(job_id)
            if not data:
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
                return

            await asyncio.sleep(1.0)

    return StreamingResponse(event_stream(), media_type="text/event-stream")
