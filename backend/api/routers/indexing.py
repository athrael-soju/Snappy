import os
import tempfile
import uuid
from typing import List
import asyncio
import json
import logging
import aiofiles
import aiofiles.os
from fastapi.responses import StreamingResponse

from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks

from api.dependencies import get_qdrant_service, qdrant_init_error
from api.utils import convert_pdf_paths_to_images_streaming
from api.progress import progress_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["indexing"])


@router.post("/index")
async def index(background_tasks: BackgroundTasks, files: List[UploadFile] = File(...)):
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    temp_paths: List[str] = []
    original_filenames: dict[str, str] = {}  # Map temp path -> original filename
    try:
        # Stream files to disk in chunks (async I/O to avoid blocking event loop)
        for uf in files:
            suffix = os.path.splitext(uf.filename or "")[1] or ".pdf"
            # Create temp file synchronously (fast operation)
            tmp_fd = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
            tmp_path = tmp_fd.name
            tmp_fd.close()  # Close sync file handle
            
            # Write async in chunks to avoid blocking
            async with aiofiles.open(tmp_path, 'wb') as tmp:
                while chunk := await uf.read(1024 * 1024):  # 1MB chunks
                    await tmp.write(chunk)
            
            temp_paths.append(tmp_path)
            original_filenames[tmp_path] = uf.filename or "document.pdf"

        # Quick validation: check service availability
        svc = get_qdrant_service()
        if not svc:
            raise HTTPException(
                status_code=503,
                detail=f"Service unavailable: {qdrant_init_error or 'Dependency services are down'}",
            )

        # Start with rough estimate (will be updated during conversion)
        job_id = str(uuid.uuid4())
        estimated_total = len(temp_paths) * 10  # Rough estimate: 10 pages per file
        
        progress_manager.create(job_id, total=estimated_total)
        progress_manager.start(job_id)

        class CancellationError(Exception):
            """Custom exception for job cancellation"""
            pass

        # Track progress offset for chunked processing
        progress_offset = {"value": 0}
        
        def progress_cb(current: int, info: dict | None = None):
            # Check for cancellation before updating progress
            if progress_manager.is_cancelled(job_id):
                raise CancellationError("Job cancelled by user")
            
            # Skip updating progress for cancellation checks only
            if info and info.get("stage") == "check_cancel":
                return
            
            # Add offset for chunked processing
            actual_current = progress_offset["value"] + current
            
            # Get the current total from progress_manager (dynamically updated)
            job_data = progress_manager.get(job_id)
            current_total = job_data.get("total", 1) if job_data else 1
            
            # Calculate percentage
            percentage = int((actual_current / current_total) * 100) if current_total > 0 else 0
            
            msg = None
            if info and "stage" in info:
                stage_name = info['stage'].capitalize()
                msg = f"{stage_name} - {actual_current}/{current_total} ({percentage}%)"
            progress_manager.update(job_id, current=actual_current, message=msg)

        def run_job(paths: List[str], filenames_map: dict[str, str]):
            try:
                # Process in chunks: convert batch -> index batch -> repeat
                # This keeps memory usage low by not holding all images at once
                chunk_size = 50  # Convert and index 50 pages at a time
                images_chunk = []
                conversion_count = 0
                total_indexed = 0
                last_known_total = estimated_total
                
                for page_dict, total_pages in convert_pdf_paths_to_images_streaming(paths, filenames_map, batch_size=20):
                    images_chunk.append(page_dict)
                    conversion_count += 1
                    
                    # Update total if it changed
                    if total_pages != last_known_total:
                        progress_manager.set_total(job_id, total_pages)
                        last_known_total = total_pages
                    
                    # When chunk is full, index it immediately
                    if len(images_chunk) >= chunk_size:
                        pct = int((total_indexed / last_known_total) * 100) if last_known_total > 0 else 0
                        progress_manager.update(job_id, current=total_indexed, message=f"Indexing chunk - {total_indexed}/{last_known_total} ({pct}%)")
                        progress_offset["value"] = total_indexed  # Update offset for progress tracking
                        svc.index_documents(images_chunk, progress_cb=progress_cb)
                        total_indexed += len(images_chunk)
                        images_chunk = []  # Clear chunk to free memory
                        
                        # Check for cancellation
                        if progress_manager.is_cancelled(job_id):
                            raise CancellationError("Job cancelled during indexing")
                
                # Index remaining pages
                if images_chunk:
                    pct = int((total_indexed / last_known_total) * 100) if last_known_total > 0 else 0
                    progress_manager.update(job_id, current=total_indexed, message=f"Indexing final chunk - {total_indexed}/{last_known_total} ({pct}%)")
                    progress_offset["value"] = total_indexed  # Update offset
                    svc.index_documents(images_chunk, progress_cb=progress_cb)
                    total_indexed += len(images_chunk)
                
                msg = f"Uploaded and indexed {total_indexed} pages"
                # Check if job was cancelled during execution
                if progress_manager.is_cancelled(job_id):
                    # Already marked as cancelled, no need to complete
                    pass
                else:
                    progress_manager.complete(job_id, message=msg)
            except CancellationError as e:
                # Cancellation - already marked by progress_manager.cancel()
                logger.info(f"Job {job_id} was cancelled: {e}")
                pass
            except Exception as e:
                # Only mark as failed if not already cancelled
                if not progress_manager.is_cancelled(job_id):
                    progress_manager.fail(job_id, error=str(e))
            finally:
                for p in paths:
                    try:
                        os.unlink(p)
                    except Exception:
                        pass

        background_tasks.add_task(run_job, list(temp_paths), dict(original_filenames))
        return {"status": "started", "job_id": job_id, "total": estimated_total}
    except Exception:
        for p in temp_paths:
            try:
                os.unlink(p)
            except Exception:
                pass
        raise


@router.post("/index/cancel/{job_id}")
async def cancel_upload(job_id: str):
    """Cancel an ongoing upload/indexing job."""
    success = progress_manager.cancel(job_id)
    if success:
        return {"status": "cancelled", "job_id": job_id, "message": "Upload cancelled successfully"}
    else:
        job_data = progress_manager.get(job_id)
        if not job_data:
            raise HTTPException(status_code=404, detail="Job not found")
        else:
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot cancel job in status: {job_data.get('status')}"
            )


@router.get("/progress/stream/{job_id}")
async def stream_progress(job_id: str):
    async def event_stream():
        last_current = None
        last_status = None
        # Send an initial snapshot if available
        while True:
            data = progress_manager.get(job_id)
            if not data:
                # Emit a terminal not_found event and stop
                yield f"event: not_found\n" + f"data: {json.dumps({'job_id': job_id})}\n\n"
                return
            total = max(1, int(data.get("total") or 0))
            try:
                pct = int(round(((int(data.get("current") or 0) / total) * 100))) if data.get("total") else 0
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

            # Emit only on change or periodically as heartbeat
            changed = (payload["current"] != (last_current if last_current is not None else -1)) or (
                payload["status"] != last_status
            )
            if changed:
                yield "event: progress\n" + f"data: {json.dumps(payload)}\n\n"
                last_current = payload["current"]
                last_status = payload["status"]
            else:
                # Heartbeat every 5 seconds to keep the connection alive
                yield "event: heartbeat\n" + "data: {}\n\n"

            # Stop on terminal states
            if payload["status"] in ("completed", "failed", "cancelled"):
                return

            await asyncio.sleep(1.0)

    return StreamingResponse(event_stream(), media_type="text/event-stream")
