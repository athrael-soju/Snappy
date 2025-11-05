import threading
import time
from typing import Dict, Optional


class ProgressManager:
    """
    Simple in-memory progress manager. Not persistent; suitable for a single-process dev setup.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._jobs: Dict[str, Dict] = {}
        self._cancel_flags: Dict[str, bool] = {}  # Track cancellation requests

    def create(self, job_id: str, total: int = 0):
        with self._lock:
            self._jobs[job_id] = {
                "job_id": job_id,
                "total": int(total) if total else 0,
                "current": 0,
                "status": "pending",  # pending | running | completed | failed | cancelled
                "message": None,
                "started_at": time.time(),
                "finished_at": None,
                "error": None,
                "details": None,
            }
            self._cancel_flags[job_id] = False  # Initialize cancel flag

    def set_total(self, job_id: str, total: int):
        with self._lock:
            if job_id in self._jobs:
                self._jobs[job_id]["total"] = int(total)

    def start(self, job_id: str):
        with self._lock:
            if job_id in self._jobs:
                self._jobs[job_id]["status"] = "running"

    def update(
        self,
        job_id: str,
        current: int,
        message: Optional[str] = None,
        details: Optional[Dict] = None,
    ):
        with self._lock:
            if job_id in self._jobs:
                self._jobs[job_id]["current"] = int(current)
                if message is not None:
                    self._jobs[job_id]["message"] = message
                if details is not None:
                    self._jobs[job_id]["details"] = details

    def complete(self, job_id: str, message: Optional[str] = None):
        with self._lock:
            if job_id in self._jobs:
                self._jobs[job_id]["status"] = "completed"
                self._jobs[job_id]["finished_at"] = time.time()
                if message is not None:
                    self._jobs[job_id]["message"] = message
        self._schedule_cleanup(job_id)

    def fail(self, job_id: str, error: str):
        with self._lock:
            if job_id in self._jobs:
                self._jobs[job_id]["status"] = "failed"
                self._jobs[job_id]["finished_at"] = time.time()
                self._jobs[job_id]["error"] = error
        self._schedule_cleanup(job_id)

    def get(self, job_id: str) -> Optional[Dict]:
        with self._lock:
            job = self._jobs.get(job_id)
            return job.copy() if job is not None else None

    def cancel(self, job_id: str) -> bool:
        """Request cancellation of a job. Returns True if job exists and can be cancelled."""
        cancelled = False
        with self._lock:
            if job_id in self._jobs:
                status = self._jobs[job_id]["status"]
                # Can only cancel running or pending jobs
                if status in ("pending", "running"):
                    self._cancel_flags[job_id] = True
                    self._jobs[job_id]["status"] = "cancelled"
                    self._jobs[job_id]["finished_at"] = time.time()
                    self._jobs[job_id]["message"] = "Upload cancelled by user"
                    cancelled = True
        if cancelled:
            self._schedule_cleanup(job_id)
        return cancelled

    def is_cancelled(self, job_id: str) -> bool:
        """Check if a job has been cancelled."""
        with self._lock:
            return self._cancel_flags.get(job_id, False)

    def cleanup(self, job_id: str):
        """Remove job data (call after job completion/cancellation)."""
        with self._lock:
            self._jobs.pop(job_id, None)
            self._cancel_flags.pop(job_id, None)

    def _schedule_cleanup(self, job_id: str, delay: float = 300.0):
        """Schedule cleanup after a delay to allow clients to read final status."""
        timer = threading.Timer(delay, self.cleanup, args=(job_id,))
        timer.daemon = True
        timer.start()


progress_manager = ProgressManager()
