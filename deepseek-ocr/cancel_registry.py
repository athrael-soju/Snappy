"""
Cancel Registry for OCR Jobs
Manages cancellation flags for cooperative job cancellation
"""

import asyncio
from typing import Optional

# Global registry: job_id -> asyncio.Event
CANCEL_FLAGS: dict[str, asyncio.Event] = {}
_cancel_lock = asyncio.Lock()


def new_cancel_flag(job_id: str) -> asyncio.Event:
    """Create a new cancellation flag for a job"""

    async def _create():
        async with _cancel_lock:
            ev = asyncio.Event()
            CANCEL_FLAGS[job_id] = ev
            return ev

    # Run in event loop if available, otherwise create synchronously
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            ev = asyncio.Event()
            asyncio.create_task(_create_sync(job_id, ev))
            return ev
        else:
            return loop.run_until_complete(_create())
    except RuntimeError:
        # No event loop, create directly
        ev = asyncio.Event()
        CANCEL_FLAGS[job_id] = ev
        return ev


async def _create_sync(job_id: str, ev: asyncio.Event):
    """Helper to register event"""
    async with _cancel_lock:
        CANCEL_FLAGS[job_id] = ev


def get_cancel_flag(job_id: str) -> Optional[asyncio.Event]:
    """Get cancellation flag for a job"""
    return CANCEL_FLAGS.get(job_id)


def cancel_job(job_id: str) -> bool:
    """Cancel a job by setting its flag. Returns True if job exists."""
    ev = CANCEL_FLAGS.get(job_id)
    if ev:
        ev.set()
        return True
    return False


async def is_cancelled(job_id: str) -> bool:
    """Check if a job has been cancelled"""
    ev = CANCEL_FLAGS.get(job_id)
    if ev:
        return ev.is_set()
    return False


def remove_cancel_flag(job_id: str):
    """Remove cancellation flag (cleanup after job completes)"""

    async def _remove():
        async with _cancel_lock:
            CANCEL_FLAGS.pop(job_id, None)

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(_remove())
        else:
            loop.run_until_complete(_remove())
    except RuntimeError:
        # No event loop, remove directly
        CANCEL_FLAGS.pop(job_id, None)
