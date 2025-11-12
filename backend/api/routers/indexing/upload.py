from __future__ import annotations

import logging
import os
import tempfile
import uuid
from typing import Dict, List

from api.dependencies import get_qdrant_service, qdrant_init_error
from api.progress import progress_manager
from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile
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


async def _persist_upload_to_disk(
    upload: UploadFile,
    chunk_size: int,
    max_file_size_bytes: int,
    max_file_size_mb: int,
) -> str:
    """Persist upload chunks to a temporary file and return the path."""
    suffix = os.path.splitext(upload.filename or "")[1] or ".pdf"

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        written_bytes = 0
        while True:
            chunk = await upload.read(chunk_size)
            if not chunk:
                break
            written_bytes += len(chunk)
            if written_bytes > max_file_size_bytes:
                await upload.close()
                tmp.close()
                raise HTTPException(
                    status_code=413,
                    detail=(
                        f"File '{upload.filename or 'unnamed'}' exceeds the maximum "
                        f"allowed size of {max_file_size_mb} MB."
                    ),
                )
            tmp.write(chunk)

        return tmp.name


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

    logger.info(
        "Document upload started",
        extra={
            "operation": "index",
            "file_count": len(files),
            "filenames": filenames,
        },
    )

    constraints = resolve_upload_constraints()
    if len(files) > constraints.max_files:
        logger.warning(
            "Upload rejected: too many files",
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
            "Files validated and persisted",
            extra={
                "operation": "index",
                "file_count": len(temp_paths),
                "duration_ms": timer.duration_ms,
            },
        )

        # Fail fast if dependencies are unavailable
        if not get_qdrant_service():
            logger.error(
                "Qdrant service unavailable",
                extra={
                    "operation": "index",
                    "error": qdrant_init_error or "Dependency services are down",
                },
            )
            raise HTTPException(
                status_code=503,
                detail=f"Service unavailable: {qdrant_init_error or 'Dependency services are down'}",
            )

        job_id = str(uuid.uuid4())
        progress_manager.create(job_id, total=0)
        progress_manager.start(job_id)

        background_tasks.add_task(
            run_indexing_job, job_id, list(temp_paths), dict(original_filenames)
        )

        logger.info(
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
