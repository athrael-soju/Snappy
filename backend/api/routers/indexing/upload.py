from __future__ import annotations

import logging
import os
import tempfile
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List

import config
from api.dependencies import get_duckdb_service, get_qdrant_service, qdrant_init_error
from api.progress import progress_manager
from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile
from pdf2image import pdfinfo_from_path
from utils.timing import PerformanceTimer

from .file_constraints import (
    UploadConstraints,
    get_upload_chunk_size_mbytes,
    is_allowed_file,
    resolve_upload_constraints,
)
from .jobs import cleanup_temp_files, run_indexing_job

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["indexing"])


def _check_file_duplicate(
    tmp_path: str, filename: str, duckdb_svc
) -> tuple[str, str, bool, dict | None]:
    """Check if a file is a duplicate.

    Args:
        tmp_path: Temporary file path
        filename: Original filename
        duckdb_svc: DuckDB service instance

    Returns:
        Tuple of (tmp_path, filename, is_duplicate, existing_doc)
    """
    try:
        # Get PDF metadata
        info = pdfinfo_from_path(tmp_path)
        pages = int(info.get("Pages", 0))
        size_bytes = os.path.getsize(tmp_path)

        # Check for duplicates
        existing_doc = duckdb_svc.check_document_exists(
            filename=filename,
            file_size_bytes=size_bytes,
            total_pages=pages,
        )

        if existing_doc:
            logger.info(
                f"Skipping already indexed document: {filename} "
                f"(first indexed: {existing_doc.get('first_indexed')})",
                extra={"operation": "index"},
            )
            # Clean up temp file for duplicate
            try:
                os.unlink(tmp_path)
            except Exception as cleanup_exc:
                logger.warning(
                    f"Failed to clean up duplicate temp file {tmp_path}: {cleanup_exc}",
                    extra={"operation": "index"},
                )
            return (tmp_path, filename, True, existing_doc)

        return (tmp_path, filename, False, None)

    except Exception as exc:
        logger.warning(
            f"Failed to check duplicate for {filename}: {exc}",
            extra={"operation": "index", "error_type": type(exc).__name__},
        )
        # If we can't get metadata, include the file anyway (fail-safe behavior)
        return (tmp_path, filename, False, None)


async def _persist_upload_to_disk(
    upload: UploadFile,
    chunk_size: int,
    max_file_size_bytes: int,
    max_file_size_mb: int,
    timeout_seconds: int = 300,
) -> str:
    """Persist upload chunks to a temporary file with proper cleanup and timeout.

    Args:
        upload: File upload to persist
        chunk_size: Size of chunks to read
        max_file_size_bytes: Maximum file size in bytes
        max_file_size_mb: Maximum file size in MB (for error message)
        timeout_seconds: Upload timeout in seconds (default: 5 minutes)

    Returns:
        Path to temporary file

    Raises:
        HTTPException: On timeout, file size exceeded, or upload failure
    """
    import asyncio
    import time

    suffix = os.path.splitext(upload.filename or "")[1] or ".pdf"
    tmp_file = None

    try:
        tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        written_bytes = 0
        start_time = time.time()

        while True:
            # Check timeout
            if time.time() - start_time > timeout_seconds:
                raise HTTPException(status_code=408, detail="Upload timeout exceeded")

            chunk = await asyncio.wait_for(
                upload.read(chunk_size), timeout=timeout_seconds
            )
            if not chunk:
                break

            written_bytes += len(chunk)
            if written_bytes > max_file_size_bytes:
                raise HTTPException(
                    status_code=413,
                    detail=(
                        f"File '{upload.filename or 'unnamed'}' exceeds the maximum "
                        f"allowed size of {max_file_size_mb} MB."
                    ),
                )

            tmp_file.write(chunk)

        tmp_file.close()
        return tmp_file.name

    except HTTPException:
        if tmp_file:
            tmp_file.close()
            try:
                os.unlink(tmp_file.name)
            except Exception as e:
                logger.warning(f"Failed to clean up temp file: {e}")
        raise
    except Exception as e:
        if tmp_file:
            tmp_file.close()
            try:
                os.unlink(tmp_file.name)
            except Exception:
                pass
        raise HTTPException(status_code=400, detail=f"Upload failed: {str(e)}")


async def _validate_and_persist_uploads(
    files: List[UploadFile],
    constraints: UploadConstraints,
) -> tuple[list[str], dict[str, str]]:
    chunk_size = get_upload_chunk_size_mbytes()
    temp_paths: list[str] = []
    original_filenames: dict[str, str] = {}

    for upload in files:
        if not is_allowed_file(upload.filename, upload.content_type, constraints):
            await upload.close()
            raise HTTPException(
                status_code=400,
                detail=(
                    f"File '{upload.filename or 'unnamed'}' is not an allowed type. "
                    f"Accepted formats: {constraints.description}."
                ),
            )

        try:
            tmp_path = await _persist_upload_to_disk(
                upload,
                chunk_size=chunk_size,
                max_file_size_bytes=constraints.max_file_size_bytes,
                max_file_size_mb=constraints.max_file_size_mb,
            )
        finally:
            await upload.close()

        temp_paths.append(tmp_path)
        original_filenames[tmp_path] = upload.filename or "document.pdf"

    return temp_paths, original_filenames


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
            temp_paths, original_filenames = await _validate_and_persist_uploads(
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
                            _check_file_duplicate,
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
