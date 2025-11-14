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
        self._cleanup_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="cleanup")
        self._job_completion_events: Dict[str, threading.Event] = {}  # Track job completion

    def create(self, job_id: str, total: int = 0, filename: Optional[str] = None, filenames: Optional[list] = None):
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
            self._job_completion_events[job_id] = threading.Event()  # Create completion event

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

    def _get_job_filenames(self, job_id: str) -> list:
        """
        Extract filenames from job details.

        Returns:
            List of filenames associated with the job
        """
        job = self._jobs.get(job_id)
        if not job or not job.get("details"):
            return []

        details = job["details"]
        # Handle both single filename and list of filenames
        if "filenames" in details:
            return details["filenames"]
        elif "filename" in details:
            return [details["filename"]]
        return []

    def _cleanup_job_services(self, job_id: str, filenames: list) -> None:
        """
        Background task to cleanup services for a job.

        This runs in a separate thread to avoid blocking the main request.
        IMPORTANT: Waits for the background job to actually stop before cleaning up.

        Args:
            job_id: Job identifier
            filenames: List of filenames to cleanup
        """
        try:
            # Import clients and create cancellation service with proper dependencies
            from domain.pipeline.cancellation import CancellationService
            from api.dependencies import get_colpali_client, get_ocr_service

            colpali_client = get_colpali_client()
            ocr_client = get_ocr_service()

            # Create cancellation service with clients for service restart capability
            cancellation_service = CancellationService(
                colpali_client=colpali_client,
                ocr_client=ocr_client
            )

            # IMMEDIATELY restart services to stop any ongoing processing
            logger.info(f"Restarting services immediately for job {job_id}")
            restart_results = cancellation_service.restart_services(
                job_id=job_id,
                wait_for_restart=True,  # Wait for services to come back up
                timeout=20  # Max 20s per service
            )
            logger.info(f"Service restart results: {restart_results}")

            # Check if restarts succeeded
            colpali_ok = restart_results.get("colpali", {}).get("success", False)
            ocr_ok = restart_results.get("deepseek_ocr", {}).get("success", False)
            if colpali_ok and ocr_ok:
                logger.info("Both services restarted successfully")
            elif colpali_ok:
                logger.warning("ColPali restarted but DeepSeek OCR failed")
            elif ocr_ok:
                logger.warning("DeepSeek OCR restarted but ColPali failed")
            else:
                logger.error("Both services failed to restart")

            # Now wait for the background job to actually complete/stop
            completion_event = self._job_completion_events.get(job_id)
            if completion_event:
                logger.info(f"Waiting for job {job_id} to stop before cleanup...")
                # Wait up to 60 seconds for job to stop
                if completion_event.wait(timeout=60):
                    logger.info(f"Job {job_id} has stopped, starting cleanup")
                else:
                    logger.warning(f"Timeout waiting for job {job_id} to stop, proceeding with cleanup anyway")
            else:
                logger.warning(f"No completion event for job {job_id}, proceeding with cleanup immediately")

            # Now cleanup the data (without restarting services again)
            cleanup_results = []
            for filename in filenames:
                if filename:
                    logger.info(f"Cleaning up services for job {job_id}, filename: {filename}")
                    results = cancellation_service.cleanup_job_data(
                        job_id=job_id,
                        filename=filename,
                        restart_services=False  # Already restarted above
                    )
                    cleanup_results.append(results)

            logger.info(
                f"Background service cleanup completed for job {job_id}",
                extra={"job_id": job_id, "cleanup_results": cleanup_results},
            )
        except Exception as exc:
            logger.error(
                f"Background service cleanup failed for job {job_id}: {exc}",
                extra={"job_id": job_id},
                exc_info=True
            )

    def fail(self, job_id: str, error: str):
        with self._lock:
            if job_id in self._jobs:
                self._jobs[job_id]["status"] = "failed"
                self._jobs[job_id]["finished_at"] = time.time()
                self._jobs[job_id]["error"] = error

        # Signal that job has failed (stopped)
        if job_id in self._job_completion_events:
            self._job_completion_events[job_id].set()

        # Schedule cleanup in background thread (non-blocking)
        filenames = self._get_job_filenames(job_id)
        if filenames:
            logger.info(f"Scheduling background cleanup for failed job {job_id}")
            self._cleanup_executor.submit(self._cleanup_job_services, job_id, filenames)
        else:
            logger.warning(f"No filenames found for failed job {job_id}, skipping service cleanup")

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
                    self._jobs[job_id]["status"] = "cancelled"
                    self._jobs[job_id]["finished_at"] = time.time()
                    self._jobs[job_id]["message"] = "Upload cancelled by user"
                    cancelled = True

        logger.info(
            f"Cancel request for job {job_id}: status={job_status}, cancelled={cancelled}",
            extra={"job_id": job_id, "status": job_status, "cancelled": cancelled}
        )

        if cancelled:
            # Schedule cleanup in background thread (non-blocking)
            filenames = self._get_job_filenames(job_id)
            logger.info(
                f"Retrieved filenames for cancelled job {job_id}: {filenames}",
                extra={"job_id": job_id, "filenames": filenames}
            )
            if filenames:
                logger.info(f"Scheduling background cleanup for cancelled job {job_id}")
                self._cleanup_executor.submit(self._cleanup_job_services, job_id, filenames)
            else:
                logger.warning(f"No filenames found for cancelled job {job_id}, skipping service cleanup")

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
