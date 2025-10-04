import os
import tempfile
import uuid
from typing import List
import asyncio
import json
import logging
from fastapi.responses import StreamingResponse

from fastapi import APIRouter, UploadFile, File, HTTPException

from api.dependencies import get_qdrant_service, get_minio_service, qdrant_init_error
from ingestion import sse_manager, IngestionOrchestrator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["indexing"])

# Global orchestrator instance (initialized on first use)
_orchestrator: IngestionOrchestrator = None


async def _get_orchestrator() -> IngestionOrchestrator:
    """Get or create orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        qdrant_svc = get_qdrant_service()
        minio_svc = get_minio_service()
        if not qdrant_svc:
            raise HTTPException(
                status_code=503,
                detail=f"Qdrant service unavailable: {qdrant_init_error or 'Service is down'}",
            )
        if not minio_svc:
            raise HTTPException(status_code=503, detail="MinIO service unavailable")
            
        # Get embedding processor and muvera from qdrant service
        embedding_processor = qdrant_svc.embedding_processor
        muvera_post = qdrant_svc.muvera_post
        
        _orchestrator = IngestionOrchestrator(
            qdrant_service=qdrant_svc,
            minio_service=minio_svc,
            embedding_processor=embedding_processor,
            muvera_post=muvera_post,
        )
        await _orchestrator.initialize()
        
    return _orchestrator


@router.post("/index")
async def index(files: List[UploadFile] = File(...)):
    """
    Upload and index files. Returns 202 Accepted with job_id.
    Use /sse/ingestion/{job_id} to track progress.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    # Save uploaded files to temp storage
    temp_paths: List[str] = []
    original_filenames: dict[str, str] = {}
    
    try:
        for uf in files:
            suffix = os.path.splitext(uf.filename or "")[1] or ".pdf"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                data = await uf.read()
                tmp.write(data)
                temp_paths.append(tmp.name)
                original_filenames[tmp.name] = uf.filename or "document.pdf"

        # Generate job ID
        job_id = str(uuid.uuid4())
        
        # Get orchestrator
        orchestrator = await _get_orchestrator()
        
        # Kickoff ingestion in background
        async def run_ingestion():
            try:
                await orchestrator.ingest_files(job_id, temp_paths, original_filenames)
            except Exception as e:
                logger.exception(f"Job {job_id} failed: {e}")
            finally:
                # Cleanup temp files
                for p in temp_paths:
                    try:
                        os.unlink(p)
                    except Exception:
                        pass
                        
        # Start background task
        asyncio.create_task(run_ingestion())
        
        # Return 202 Accepted immediately
        return {
            "status": "accepted",
            "job_id": job_id,
            "file_count": len(files),
            "message": f"Indexing {len(files)} files"
        }
        
    except Exception as e:
        # Cleanup on error
        for p in temp_paths:
            try:
                os.unlink(p)
            except Exception:
                pass
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/sse/ingestion/{job_id}")
async def stream_ingestion_progress(job_id: str):
    """
    Server-Sent Events endpoint for ingestion progress.
    Returns events: queued, intake, image, embed, index, storage, completed, error.
    """
    async def event_stream():
        queue = await sse_manager.subscribe(job_id)
        
        try:
            # Send initial state if available
            initial_state = sse_manager.get_job_state(job_id)
            if initial_state:
                yield f"event: progress\ndata: {json.dumps(initial_state)}\n\n"
            else:
                # Job not found or not started yet
                yield f"event: waiting\ndata: {json.dumps({'job_id': job_id, 'message': 'Waiting for job to start'})}\n\n"
            
            heartbeat_counter = 0
            while True:
                try:
                    # Wait for next event with timeout for heartbeat
                    event = await asyncio.wait_for(queue.get(), timeout=5.0)
                    
                    # Emit progress event
                    yield f"event: progress\ndata: {json.dumps(event)}\n\n"
                    
                    # Check for terminal states
                    if event.get("stage") in ["completed", "error"]:
                        break
                        
                except asyncio.TimeoutError:
                    # Send heartbeat every 5 seconds
                    heartbeat_counter += 1
                    yield f"event: heartbeat\ndata: {json.dumps({'count': heartbeat_counter})}\n\n"
                    
        except Exception as e:
            logger.error(f"SSE error for job {job_id}: {e}")
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"
        finally:
            await sse_manager.unsubscribe(job_id, queue)
            
    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post("/index/cancel/{job_id}")
async def cancel_ingestion(job_id: str):
    """
    Cancel an ongoing ingestion job (best effort).
    Note: Cancellation is not fully implemented in the concurrent pipeline yet.
    """
    # For now, just emit an error event to stop SSE clients
    await sse_manager.emit_error(job_id, "Job cancelled by user")
    return {"status": "cancelled", "job_id": job_id, "message": "Cancellation signal sent"}
