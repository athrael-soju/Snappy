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

    def create(self, job_id: str, total: int = 0):
        with self._lock:
            self._jobs[job_id] = {
                "job_id": job_id,
                "total": int(total) if total else 0,
                "current": 0,
                "status": "pending",  # pending | running | completed | failed
                "message": None,
                "started_at": time.time(),
                "finished_at": None,
                "error": None,
            }

    def set_total(self, job_id: str, total: int):
        with self._lock:
            if job_id in self._jobs:
                self._jobs[job_id]["total"] = int(total)

    def start(self, job_id: str):
        with self._lock:
            if job_id in self._jobs:
                self._jobs[job_id]["status"] = "running"

    def update(self, job_id: str, current: int, message: Optional[str] = None):
        with self._lock:
            if job_id in self._jobs:
                self._jobs[job_id]["current"] = int(current)
                if message is not None:
                    self._jobs[job_id]["message"] = message

    def complete(self, job_id: str, message: Optional[str] = None):
        with self._lock:
            if job_id in self._jobs:
                self._jobs[job_id]["status"] = "completed"
                self._jobs[job_id]["finished_at"] = time.time()
                if message is not None:
                    self._jobs[job_id]["message"] = message

    def fail(self, job_id: str, error: str):
        with self._lock:
            if job_id in self._jobs:
                self._jobs[job_id]["status"] = "failed"
                self._jobs[job_id]["finished_at"] = time.time()
                self._jobs[job_id]["error"] = error

    def get(self, job_id: str) -> Optional[Dict]:
        with self._lock:
            return dict(self._jobs.get(job_id)) if job_id in self._jobs else None


progress_manager = ProgressManager()
