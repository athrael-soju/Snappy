from __future__ import annotations

import logging
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List

import config
from api.dependencies import get_duckdb_service, get_qdrant_service, qdrant_init_error
from api.progress import progress_manager
from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile
from utils.timing import PerformanceTimer

from domain.file_constraints import (
    UploadConstraints,
    resolve_upload_constraints,
)
from domain.indexing import check_file_duplicate, validate_and_persist_uploads
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

        # Check for duplicates before starting background job (parallelized)
        duckdb_svc = get_duckdb_service()
        if duckdb_svc and duckdb_svc.is_enabled():
            with PerformanceTimer(
                "deduplication check", log_on_exit=False
            ) as dup_timer:
                filtered_paths: List[str] = []
                filtered_filenames: Dict[str, str] = {}
                skipped_files: List[str] = []

                # Parallelize duplicate checking for better performance
                # Use batch size for consistency with pipeline parallelism
                max_workers = min(
                    len(temp_paths),
                    max(1, int(config.BATCH_SIZE)),
                )
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    # Submit all duplicate checks in parallel
                    future_to_path = {
                        executor.submit(
                            check_file_duplicate,
                            tmp_path,
                            original_filenames[tmp_path],
                            duckdb_svc,
                        ): tmp_path
                        for tmp_path in temp_paths
                    }

                    # Collect results as they complete
                    for future in as_completed(future_to_path):
                        try:
                            tmp_path, filename, is_duplicate, existing_doc = (
                                future.result()
                            )

                            if is_duplicate:
                                skipped_files.append(filename)
                            else:
                                filtered_paths.append(tmp_path)
                                filtered_filenames[tmp_path] = filename
                        except Exception as exc:
                            # If duplicate check fails, include the file (fail-safe)
                            tmp_path = future_to_path[future]
                            filename = original_filenames[tmp_path]
                            logger.error(
                                f"Duplicate check failed for {filename}: {exc}",
                                exc_info=True,
                                extra={"operation": "index"},
                            )
                            filtered_paths.append(tmp_path)
                            filtered_filenames[tmp_path] = filename

                # Update lists to only include non-duplicates
                temp_paths = filtered_paths
                original_filenames = filtered_filenames

                if skipped_files:
                    logger.info(
                        f"Skipped {len(skipped_files)} already indexed documents (deduplication took {dup_timer.duration_s:.2f}s)",
                        extra={
                            "operation": "index",
                            "skipped_files": skipped_files,
                            "duration_s": round(dup_timer.duration_s, 3),
                        },
                    )

                # If all files were duplicates, return early
                if not temp_paths:
                    return {
                        "status": "completed",
                        "message": "All documents already indexed (skipped)",
                        "skipped_count": len(skipped_files),
                        "skipped_files": skipped_files,
                    }

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
