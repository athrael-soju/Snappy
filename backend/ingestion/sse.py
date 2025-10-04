"""Server-Sent Events (SSE) manager for ingestion progress."""

import asyncio
import json
import logging
from typing import Dict, Optional, Set
from collections import defaultdict
from .models import ProgressEvent, StageType

logger = logging.getLogger(__name__)


class SSEManager:
    """Manages SSE connections and progress events for ingestion jobs."""
    
    def __init__(self):
        self._subscribers: Dict[str, Set[asyncio.Queue]] = defaultdict(set)
        self._lock = asyncio.Lock()
        self._job_states: Dict[str, dict] = {}  # Track latest state per job
        
    async def subscribe(self, job_id: str) -> asyncio.Queue:
        """Subscribe to events for a specific job."""
        queue = asyncio.Queue(maxsize=100)
        async with self._lock:
            self._subscribers[job_id].add(queue)
            # Send initial state if available
            if job_id in self._job_states:
                try:
                    await queue.put(self._job_states[job_id])
                except asyncio.QueueFull:
                    pass
        return queue
        
    async def unsubscribe(self, job_id: str, queue: asyncio.Queue):
        """Unsubscribe from job events."""
        async with self._lock:
            if job_id in self._subscribers:
                self._subscribers[job_id].discard(queue)
                if not self._subscribers[job_id]:
                    del self._subscribers[job_id]
                    
    async def emit(self, event: ProgressEvent):
        """Emit a progress event to all subscribers."""
        job_id = event.job_id
        event_dict = event.to_dict()
        
        async with self._lock:
            # Update job state
            self._job_states[job_id] = event_dict
            
            if job_id not in self._subscribers:
                return
                
            # Send to all subscribers
            dead_queues = set()
            for queue in self._subscribers[job_id]:
                try:
                    await asyncio.wait_for(queue.put(event_dict), timeout=0.1)
                except (asyncio.QueueFull, asyncio.TimeoutError):
                    logger.warning(f"Queue full for job {job_id}, dropping event")
                except Exception as e:
                    logger.error(f"Error sending event to queue: {e}")
                    dead_queues.add(queue)
                    
            # Clean up dead queues
            for queue in dead_queues:
                self._subscribers[job_id].discard(queue)
                
    async def emit_queued(self, job_id: str, file_count: int):
        """Emit queued event."""
        await self.emit(ProgressEvent(
            job_id=job_id,
            stage=StageType.QUEUED,
            counts={"files": file_count},
            message="Job queued"
        ))
        
    async def emit_intake(self, job_id: str, file_id: str, filename: str):
        """Emit intake event."""
        await self.emit(ProgressEvent(
            job_id=job_id,
            stage=StageType.INTAKE,
            file_id=file_id,
            message=f"Processing {filename}"
        ))
        
    async def emit_image(self, job_id: str, file_id: str, done: int, total: int):
        """Emit image generation event."""
        await self.emit(ProgressEvent(
            job_id=job_id,
            stage=StageType.IMAGE,
            file_id=file_id,
            counts={"done": done, "total": total}
        ))
        
    async def emit_embed(self, job_id: str, file_id: str, done: int, total: int):
        """Emit embedding event."""
        await self.emit(ProgressEvent(
            job_id=job_id,
            stage=StageType.EMBED,
            file_id=file_id,
            counts={"done": done, "total": total}
        ))
        
    async def emit_index(self, job_id: str, file_id: str, done: int, total: int):
        """Emit indexing event."""
        await self.emit(ProgressEvent(
            job_id=job_id,
            stage=StageType.INDEX,
            file_id=file_id,
            counts={"done": done, "total": total}
        ))
        
    async def emit_storage(self, job_id: str, file_id: str, done: int, total: int):
        """Emit storage event."""
        await self.emit(ProgressEvent(
            job_id=job_id,
            stage=StageType.STORAGE,
            file_id=file_id,
            counts={"done": done, "total": total}
        ))
        
    async def emit_completed(self, job_id: str, total_pages: int):
        """Emit completion event."""
        await self.emit(ProgressEvent(
            job_id=job_id,
            stage=StageType.COMPLETED,
            counts={"total_pages": total_pages},
            message=f"Indexed {total_pages} pages successfully"
        ))
        
    async def emit_error(self, job_id: str, error: str, file_id: Optional[str] = None):
        """Emit error event."""
        await self.emit(ProgressEvent(
            job_id=job_id,
            stage=StageType.ERROR,
            file_id=file_id,
            error=error,
            message="Job failed"
        ))
        
    async def cleanup_job(self, job_id: str):
        """Clean up job state and subscribers."""
        async with self._lock:
            self._job_states.pop(job_id, None)
            self._subscribers.pop(job_id, None)
            
    def get_job_state(self, job_id: str) -> Optional[dict]:
        """Get the latest state for a job."""
        return self._job_states.get(job_id)


# Global SSE manager instance
sse_manager = SSEManager()
