from __future__ import annotations

import asyncio
import logging
import os
import tempfile
import time
from typing import Dict, List, Optional, Protocol
from uuid import uuid4

import config
from api.dependencies import get_qdrant_service, qdrant_init_error
from api.progress import progress_manager
from clients.qdrant.indexing.points import PointFactory
from domain.errors import (
    FileSizeExceededError,
    InvalidFileTypeError,
    UploadError,
    UploadTimeoutError,
)
from domain.file_constraints import (
    UploadConstraints,
    get_upload_chunk_size_mbytes,
    is_allowed_file,
)
from domain.pipeline.errors import CancellationError
from domain.pipeline.streaming_pipeline import StreamingPipeline
from pdf2image import pdfinfo_from_path

logger = logging.getLogger(__name__)


class UploadFileProtocol(Protocol):
    """Protocol for file upload objects.

    This allows the domain layer to work with any upload implementation
    (FastAPI, Flask, etc.) without direct framework dependencies.
    """

    filename: Optional[str]
    content_type: Optional[str]

    async def read(self, size: int = -1) -> bytes:
        """Read bytes from the upload."""
        ...

    async def close(self) -> None:
        """Close the upload."""
        ...


async def _persist_upload_to_disk(
    upload: UploadFileProtocol,
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
        UploadTimeoutError: On timeout
        FileSizeExceededError: On file size exceeded
        UploadError: On upload failure
    """
    suffix = os.path.splitext(upload.filename or "")[1] or ".pdf"
    tmp_file = None

    try:
        tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        written_bytes = 0
        start_time = time.time()

        while True:
            # Check timeout
            if time.time() - start_time > timeout_seconds:
                raise UploadTimeoutError("Upload timeout exceeded")

            chunk = await asyncio.wait_for(
                upload.read(chunk_size), timeout=timeout_seconds
            )
            if not chunk:
                break

            written_bytes += len(chunk)
            if written_bytes > max_file_size_bytes:
                raise FileSizeExceededError(
                    f"File '{upload.filename or 'unnamed'}' exceeds the maximum "
                    f"allowed size of {max_file_size_mb} MB."
                )

            tmp_file.write(chunk)

        tmp_file.close()
        return tmp_file.name

    except (UploadTimeoutError, FileSizeExceededError):
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
        raise UploadError(f"Upload failed: {str(e)}")


async def validate_and_persist_uploads(
    files: List[UploadFileProtocol],
    constraints: UploadConstraints,
) -> tuple[list[str], dict[str, str]]:
    chunk_size = get_upload_chunk_size_mbytes()
    temp_paths: list[str] = []
    original_filenames: dict[str, str] = {}

    for upload in files:
        if not is_allowed_file(upload.filename, upload.content_type, constraints):
            await upload.close()
            raise InvalidFileTypeError(
                f"File '{upload.filename or 'unnamed'}' is not an allowed type. "
                f"Accepted formats: {constraints.description}."
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


def cleanup_temp_files(paths: List[str]) -> None:
    """Best-effort cleanup for temporary files."""
    cleanup_count = 0
    failed_count = 0

    for path in paths:
        try:
            if os.path.exists(path):
                os.unlink(path)
                cleanup_count += 1
        except Exception as exc:
            failed_count += 1
            logger.warning(f"Failed to clean up temp file {path}: {exc}")

    if cleanup_count > 0:
        logger.debug(f"Cleaned up {cleanup_count} temporary files")
    if failed_count > 0:
        logger.warning(f"Failed to clean up {failed_count} temporary files")


def run_indexing_job(
    job_id: str,
    paths: List[str],
    filenames: Dict[str, str],
) -> None:
    """
    Background task that performs streaming ingestion.

    Processes PDF pages immediately as they're rasterized for 6x faster
    ingestion with progressive results.
    """
    pipeline = None

    try:
        # Check for early cancellation
        if progress_manager.is_cancelled(job_id):
            raise CancellationError("Job cancelled before processing started")

        progress_manager.update(
            job_id,
            current=0,
            message="Initializing streaming pipeline",
        )

        # Get services
        qdrant_svc = get_qdrant_service()
        if not qdrant_svc:
            error_msg = qdrant_init_error.get() or "Dependency services are down"
            raise RuntimeError(error_msg)

        # Create image storage handler for streaming pipeline
        from domain.pipeline.image_processor import ImageProcessor
        from domain.pipeline.storage import ImageStorageHandler

        image_processor = ImageProcessor(
            default_format=config.IMAGE_FORMAT,
            default_quality=config.IMAGE_QUALITY,
        )
        image_store = ImageStorageHandler(
            storage_service=qdrant_svc.storage_service,
            image_processor=image_processor,
        )

        # Initialize streaming pipeline with all dependencies
        pipeline = StreamingPipeline(
            embedding_processor=qdrant_svc.embedding_processor,
            image_store=image_store,
            image_processor=image_processor,
            ocr_service=qdrant_svc.ocr_service,
            point_factory=PointFactory(),
            qdrant_service=qdrant_svc.service,
            collection_name=qdrant_svc.collection_name,
            storage_base_url=config.LOCAL_STORAGE_PUBLIC_URL,
            storage_bucket=config.LOCAL_STORAGE_BUCKET_NAME,
            batch_size=int(config.BATCH_SIZE),
            max_in_flight_batches=int(config.PIPELINE_MAX_IN_FLIGHT_BATCHES),
        )

        logger.info(f"Job {job_id}: Using streaming pipeline")

        # Create cancellation check function
        def check_cancellation():
            if progress_manager.is_cancelled(job_id):
                raise CancellationError("Job cancelled during processing")

        # Pre-scan all documents to get total pages and sizes for progress display
        total_pages_all = 0
        total_size_bytes = 0
        doc_filenames = []
        doc_info = {}  # path -> (pages, size_bytes)

        for pdf_path in paths:
            filename = filenames.get(pdf_path, os.path.basename(pdf_path))
            doc_filenames.append(filename)
            try:
                info = pdfinfo_from_path(pdf_path)
                pages = int(info.get("Pages", 0))
                size_bytes = os.path.getsize(pdf_path)
                doc_info[pdf_path] = (pages, size_bytes)
                total_pages_all += pages
                total_size_bytes += size_bytes
            except Exception as exc:
                logger.warning(f"Failed to get PDF info for {filename}: {exc}")
                doc_info[pdf_path] = (0, 0)

        # Initialize Rich console with job info
        from domain.pipeline.console import get_pipeline_console

        console = get_pipeline_console()
        console.start_job(
            doc_filenames, total_pages_all, total_size_bytes / 1024 / 1024
        )

        # Update progress manager with total
        if progress_manager.get(job_id):
            progress_manager.set_total(job_id, total_pages_all)

        pages_processed = 0

        # Progress callback for streaming updates
        def progress_cb(current: int):
            nonlocal pages_processed
            pages_processed = current

            progress_manager.update(
                job_id,
                current=pages_processed,
                message=f"Processing {pages_processed}/{total_pages_all} pages",
            )

        # Start consumer threads with progress callback
        pipeline.start(progress_callback=progress_cb)

        for pdf_path in paths:
            filename = filenames.get(pdf_path, os.path.basename(pdf_path))

            logger.debug("Starting streaming ingestion for: %s", filename)

            progress_manager.update(
                job_id,
                current=pages_processed,
                message=f"Processing {filename}...",
            )

            # Generate document_id and use pre-scanned info
            document_id = str(uuid4())
            total_pages, file_size_bytes = doc_info.get(pdf_path, (0, 0))

            # Process PDF through streaming pipeline with consistent document_id
            try:
                pages_in_doc = pipeline.process_pdf(
                    pdf_path=pdf_path,
                    filename=filename,
                    document_id=document_id,
                    cancellation_check=check_cancellation,
                )

                logger.debug(
                    "Streaming ingestion complete for %s: %d pages",
                    filename,
                    pages_in_doc,
                )

            except CancellationError:
                raise
            except Exception as exc:
                logger.error(
                    f"Failed to process {filename}: {exc}",
                    exc_info=True,
                )
                raise

        # Wait for pipeline to finish processing all batches
        progress_manager.update(
            job_id,
            current=pages_processed,
            message="Finalizing processing...",
        )

        # Check cancellation before waiting (to avoid blocking on cancelled job)
        if progress_manager.is_cancelled(job_id):
            raise CancellationError("Job cancelled during processing")

        pipeline.wait_for_completion()

        # Check for late cancellation
        if progress_manager.is_cancelled(job_id):
            raise CancellationError("Job cancelled after processing")

        # Success!
        completion_msg = (
            f"Successfully processed {total_pages_all} pages "
            f"from {len(paths)} document(s) using streaming pipeline"
        )

        progress_manager.complete(job_id, message=completion_msg)

        logger.info(f"Job {job_id} completed: {completion_msg}")

    except CancellationError as exc:
        logger.info(f"Job {job_id} cancelled: {exc}")
        # Signal that the background job has stopped
        progress_manager.signal_job_stopped(job_id)

    except Exception as exc:
        logger.exception(f"Job {job_id} failed", exc_info=exc)
        if not progress_manager.is_cancelled(job_id):
            progress_manager.fail(job_id, error=str(exc))

    finally:
        # Stop pipeline threads
        if pipeline:
            try:
                pipeline.stop()
            except Exception as exc:
                logger.warning(f"Error stopping pipeline: {exc}")

        # Cleanup temporary files
        cleanup_temp_files(paths)
