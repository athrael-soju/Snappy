"""
Progress Bus for SSE streaming of OCR job progress
Enables real-time progress updates without polling
"""

import asyncio
import json
import uuid
from typing import Dict


class ProgressBus:
    """Manages progress streams for async OCR jobs"""

    def __init__(self):
        self.queues: Dict[str, asyncio.Queue] = {}
        self.lock = asyncio.Lock()

    def new_job(self) -> str:
        """Create a new job and return its ID"""
        jid = uuid.uuid4().hex[:16]  # Short job ID
        asyncio.create_task(self._ensure_queue(jid))
        return jid

    async def _ensure_queue(self, jid: str):
        """Ensure queue exists for job"""
        async with self.lock:
            if jid not in self.queues:
                self.queues[jid] = asyncio.Queue()

    async def send(self, jid: str, **payload):
        """Send progress update for a job"""
        async with self.lock:
            q = self.queues.get(jid)
            if q:
                await q.put({"event": "progress", **payload})

    async def finalize(self, jid: str, **payload):
        """Finalize job and close stream"""
        async with self.lock:
            q = self.queues.get(jid)
            if q:
                await q.put({"event": "done", **payload})
                await q.put(None)  # Sentinel to close stream

    async def error(self, jid: str, error: str):
        """Send error for a job"""
        async with self.lock:
            q = self.queues.get(jid)
            if q:
                await q.put({"event": "error", "error": error})
                await q.put(None)  # Close stream on error

    async def stream(self, jid: str):
        """SSE stream for a job - yields SSE-formatted events"""
        # Ensure queue exists
        await self._ensure_queue(jid)

        q = self.queues.get(jid)
        if not q:
            yield f"data: {json.dumps({'event': 'error', 'error': 'Job not found'}, ensure_ascii=False)}\n\n"
            return

        try:
            while True:
                # Wait for next event with timeout
                try:
                    item = await asyncio.wait_for(
                        q.get(), timeout=300.0
                    )  # 5 minute timeout
                except asyncio.TimeoutError:
                    yield f"data: {json.dumps({'event': 'timeout', 'error': 'Stream timeout'}, ensure_ascii=False)}\n\n"
                    break

                if item is None:
                    break  # Sentinel - close stream

                # SSE format: data: {json}\n\n
                yield f"data: {json.dumps(item, ensure_ascii=False)}\n\n"
        finally:
            # Cleanup queue
            async with self.lock:
                self.queues.pop(jid, None)

    def cleanup(self, jid: str):
        """Remove job from bus (after completion or timeout)"""

        async def _cleanup():
            async with self.lock:
                self.queues.pop(jid, None)

        asyncio.create_task(_cleanup())


# Global progress bus instance
bus = ProgressBus()
