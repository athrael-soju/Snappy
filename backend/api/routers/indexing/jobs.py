from __future__ import annotations

import logging
import os
from typing import Dict, Iterable, List

from api.dependencies import get_qdrant_service, qdrant_init_error
from api.progress import progress_manager
from api.utils import convert_pdf_paths_to_images

logger = logging.getLogger(__name__)


class CancellationError(Exception):
    """Raised when a job is cancelled mid-flight."""


def cleanup_temp_files(paths: Iterable[str]) -> None:
    """Best-effort cleanup for temporary files."""
    for path in paths:
        try:
            os.unlink(path)
        except Exception:
            pass


def run_indexing_job(job_id: str, paths: List[str], filenames: Dict[str, str]) -> None:
    """Background task that performs the full indexing pipeline."""
    try:
        if progress_manager.is_cancelled(job_id):
            raise CancellationError("Job cancelled before processing started")

        progress_manager.update(job_id, current=0, message="converting documents")

        total_images, image_iterator = convert_pdf_paths_to_images(paths, filenames)
        progress_manager.set_total(job_id, total_images)

        svc = get_qdrant_service()
        if not svc:
            error_msg = qdrant_init_error.get() or "Dependency services are down"
            raise RuntimeError(error_msg)

        job_state = {"current": 0}

        def progress_cb(current: int, info: dict | None = None):
            if progress_manager.is_cancelled(job_id):
                raise CancellationError("Job cancelled by user")

            if info and info.get("stage") == "check_cancel":
                return

            job_state["current"] = max(job_state["current"], int(current))
            message = f"Processing {job_state['current']}/{total_images} pages"

            progress_manager.update(
                job_id,
                current=job_state["current"],
                message=message,
                details=None,
            )

        progress_manager.update(
            job_id,
            current=0,
            message=f"Starting processing of {total_images} pages...",
            details=None,
        )
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
    except Exception as exc:  # noqa: BLE001 - best-effort task protection
        if not progress_manager.is_cancelled(job_id):
            progress_manager.fail(job_id, error=str(exc))
            logger.exception("Job %s failed", job_id)
    finally:
        cleanup_temp_files(paths)


__all__ = ["CancellationError", "cleanup_temp_files", "run_indexing_job"]
