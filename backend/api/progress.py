import logging
import threading
import time
from typing import Dict, Optional
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)


class ProgressManager:
    """
    Simple in-memory progress manager. Not persistent; suitable for a single-process dev setup.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._jobs: Dict[str, Dict] = {}
        self._cancel_flags: Dict[str, bool] = {}  # Track cancellation requests
        self._timers: Dict[str, threading.Timer] = {}  # Track cleanup timers
        self._cleanup_executor = ThreadPoolExecutor(
            max_workers=2, thread_name_prefix="cleanup"
        )
        self._job_completion_events: Dict[str, threading.Event] = (
            {}
        )  # Track job completion

    def create(
        self,
        job_id: str,
        total: int = 0,
        filename: Optional[str] = None,
        filenames: Optional[list] = None,
    ):
        """
        Create a new job with optional filename tracking.

        Args:
            job_id: Unique job identifier
            total: Total items to process
            filename: Single filename (for single-file jobs)
            filenames: List of filenames (for multi-file jobs)
        """
        with self._lock:
            details = None
            if filenames:
                details = {"filenames": filenames}
            elif filename:
                details = {"filename": filename}

            self._jobs[job_id] = {
                "job_id": job_id,
                "total": int(total) if total else 0,
                "current": 0,
                "status": "pending",  # pending | running | completed | failed | cancelled
                "message": None,
                "started_at": time.time(),
                "finished_at": None,
                "error": None,
                "details": details,
            }
            self._cancel_flags[job_id] = False  # Initialize cancel flag
            self._job_completion_events[job_id] = (
                threading.Event()
            )  # Create completion event

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

        # Signal that job has completed
        if job_id in self._job_completion_events:
            self._job_completion_events[job_id].set()

        self._schedule_cleanup(job_id)

    def _cleanup_job_services(self, job_id: str) -> None:
        """
        Background task to wait for job to stop and mark as cancelled.

        This runs in a separate thread to avoid blocking the main request.
        Simply waits for the job to stop processing, no service restarts or data cleanup.

        Args:
            job_id: Job identifier
        """
        try:
            logger.info(f"Waiting for job {job_id} to stop...")

            # Wait for the background job to actually complete/stop
            completion_event = self._job_completion_events.get(job_id)
            if completion_event:
                # Wait up to 10 seconds for job to stop gracefully
                if completion_event.wait(timeout=10):
                    logger.info(f"Job {job_id} stopped gracefully")
                else:
                    logger.warning(
                        f"Job {job_id} did not stop within timeout, marking as cancelled anyway"
                    )
            else:
                logger.warning(
                    f"No completion event for job {job_id}, marking as cancelled immediately"
                )

            # Mark job as cancelled
            with self._lock:
                if (
                    job_id in self._jobs
                    and self._jobs[job_id]["status"] == "cancelling"
                ):
                    self._jobs[job_id]["status"] = "cancelled"
                    self._jobs[job_id]["finished_at"] = time.time()
                    self._jobs[job_id]["message"] = "Job cancelled"

            logger.info(f"Job {job_id} marked as cancelled")

        except Exception as exc:
            logger.error(
                f"Error marking job {job_id} as cancelled: {exc}",
                extra={"job_id": job_id},
                exc_info=True,
            )
            # Mark job as cancelled even if there was an error
            with self._lock:
                if (
                    job_id in self._jobs
                    and self._jobs[job_id]["status"] == "cancelling"
                ):
                    self._jobs[job_id]["status"] = "cancelled"
                    self._jobs[job_id]["finished_at"] = time.time()
                    self._jobs[job_id]["message"] = "Job cancelled"
                    self._jobs[job_id]["error"] = str(exc)

    def fail(self, job_id: str, error: str):
        with self._lock:
            if job_id in self._jobs:
                self._jobs[job_id]["status"] = "failed"
                self._jobs[job_id]["finished_at"] = time.time()
                self._jobs[job_id]["error"] = error

        # Signal that job has failed (stopped)
        if job_id in self._job_completion_events:
            self._job_completion_events[job_id].set()

        self._schedule_cleanup(job_id)

    def get(self, job_id: str) -> Optional[Dict]:
        with self._lock:
            job = self._jobs.get(job_id)
            return job.copy() if job is not None else None

    def cancel(self, job_id: str) -> bool:
        """Request cancellation of a job. Returns True if job exists and can be cancelled."""
        cancelled = False
        job_status = None
        with self._lock:
            if job_id in self._jobs:
                status = self._jobs[job_id]["status"]
                job_status = status
                # Can only cancel running or pending jobs
                if status in ("pending", "running"):
                    self._cancel_flags[job_id] = True
                    self._jobs[job_id]["status"] = "cancelling"
                    self._jobs[job_id]["message"] = "Cancelling job..."
                    cancelled = True

        logger.info(
            f"Cancel request for job {job_id}: status={job_status}, cancelled={cancelled}",
            extra={"job_id": job_id, "status": job_status, "cancelled": cancelled},
        )

        if cancelled:
            # Schedule cleanup in background thread (non-blocking)
            logger.info(f"Scheduling background cleanup for cancelled job {job_id}")
            self._cleanup_executor.submit(self._cleanup_job_services, job_id)
            self._schedule_cleanup(job_id)

        return cancelled

    def is_cancelled(self, job_id: str) -> bool:
        """Check if a job has been cancelled."""
        with self._lock:
            return self._cancel_flags.get(job_id, False)

    def get_active_jobs(self) -> list[str]:
        """Get list of currently running job IDs."""
        with self._lock:
            return [
                job_id
                for job_id, job in self._jobs.items()
                if job["status"] == "running"
            ]

    def signal_job_stopped(self, job_id: str):
        """
        Signal that a background job has actually stopped processing.

        This is called by the background job when it finishes/fails/cancels.
        This triggers cleanup to proceed if it was waiting.
        """
        if job_id in self._job_completion_events:
            logger.debug(f"Signaling job {job_id} has stopped")
            self._job_completion_events[job_id].set()

    def cleanup(self, job_id: str):
        """Remove job data and cancel any pending cleanup timer."""
        with self._lock:
            self._jobs.pop(job_id, None)
            self._cancel_flags.pop(job_id, None)
            self._job_completion_events.pop(job_id, None)  # Clean up completion event
            # Cancel and remove timer if it exists
            timer = self._timers.pop(job_id, None)
            if timer is not None:
                timer.cancel()

    def _schedule_cleanup(self, job_id: str, delay: float = 300.0):
        """Schedule cleanup after a delay to allow clients to read final status."""
        # Create timer first (but don't start it yet)
        timer = threading.Timer(delay, self.cleanup, args=(job_id,))
        timer.daemon = True

        # Cancel any existing timer and store new timer atomically
        with self._lock:
            existing_timer = self._timers.get(job_id)
            if existing_timer is not None:
                existing_timer.cancel()
            # Store timer before starting to avoid race condition
            self._timers[job_id] = timer

        # Start timer after it's been stored
        timer.start()


progress_manager = ProgressManager()
