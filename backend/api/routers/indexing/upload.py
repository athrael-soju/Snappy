from __future__ import annotations

import logging
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List

import config
from api.dependencies import get_qdrant_service, qdrant_init_error
from api.progress import progress_manager
from domain.errors import (
    FileSizeExceededError,
    InvalidFileTypeError,
    UploadError,
    UploadTimeoutError,
)
from domain.file_constraints import (
    UploadConstraints,
    resolve_upload_constraints,
)
from domain.indexing import validate_and_persist_uploads
from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile
from utils.timing import PerformanceTimer

from .jobs import cleanup_temp_files, run_indexing_job

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["indexing"])




@router.post("/index")
async def index(background_tasks: BackgroundTasks, files: List[UploadFile] = File(...)):
    if not files:
        logger.warning("Upload attempt with no files", extra={"operation": "index"})
        raise HTTPException(status_code=400, detail="No files uploaded")

    # Get file info for logging
    filenames = [f.filename or "unnamed" for f in files]

    constraints = resolve_upload_constraints()
    if len(files) > constraints.max_files:
        logger.warning(
            f"Upload rejected: {len(files)} files exceeds limit of {constraints.max_files}",
            extra={
                "operation": "index",
                "file_count": len(files),
                "max_allowed": constraints.max_files,
            },
        )
        raise HTTPException(
            status_code=400,
            detail=f"Too many files. Maximum allowed per upload is {constraints.max_files}.",
        )

    temp_paths: List[str] = []
    original_filenames: Dict[str, str] = {}

    try:
        with PerformanceTimer(
            "validate and persist uploads", log_on_exit=False
        ) as timer:
            temp_paths, original_filenames = await validate_and_persist_uploads(
                files, constraints
            )

        logger.info(
            f"Upload started: {len(files)} file(s) - {', '.join(filenames)}",
            extra={
                "operation": "index",
                "file_count": len(files),
                "filenames": filenames,
                "duration_s": round(timer.duration_s, 3),
            },
        )

        # Fail fast if dependencies are unavailable
        if not get_qdrant_service():
            error_msg = qdrant_init_error.get() or "Dependency services are down"
            logger.error(
                "Qdrant service unavailable",
                extra={
                    "operation": "index",
                    "error": error_msg,
                },
            )
            raise HTTPException(
                status_code=503,
                detail=f"Service unavailable: {error_msg}",
            )

        # Check for active jobs and warn about potential resource contention
        active_jobs = progress_manager.get_active_jobs()
        if active_jobs:
            logger.warning(
                f"Starting new upload while {len(active_jobs)} job(s) still running. "
                f"Services may still be processing previous batches.",
                extra={
                    "operation": "index",
                    "active_jobs": active_jobs,
                    "new_file_count": len(temp_paths),
                },
            )

        job_id = str(uuid.uuid4())
        # Store all filenames for potential cleanup
        filenames_list = list(original_filenames.values())
        progress_manager.create(job_id, total=0, filenames=filenames_list)
        progress_manager.start(job_id)

        background_tasks.add_task(
            run_indexing_job, job_id, list(temp_paths), dict(original_filenames)
        )

        logger.debug(
            "Indexing job queued",
            extra={
                "operation": "index",
                "job_id": job_id,
                "file_count": len(temp_paths),
                "filenames": list(original_filenames.values()),
            },
        )

        return {"status": "started", "job_id": job_id, "total": 0}

    except UploadTimeoutError as e:
        cleanup_temp_files(temp_paths)
        raise HTTPException(status_code=408, detail=str(e))
    except FileSizeExceededError as e:
        cleanup_temp_files(temp_paths)
        raise HTTPException(status_code=413, detail=str(e))
    except InvalidFileTypeError as e:
        cleanup_temp_files(temp_paths)
        raise HTTPException(status_code=400, detail=str(e))
    except UploadError as e:
        cleanup_temp_files(temp_paths)
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        cleanup_temp_files(temp_paths)
        raise
    except Exception as exc:
        logger.error(
            "Document upload failed",
            exc_info=exc,
            extra={
                "operation": "index",
                "file_count": len(files),
                "filenames": filenames,
            },
        )
        cleanup_temp_files(temp_paths)
        raise
