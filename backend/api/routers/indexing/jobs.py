"""
Streaming ingestion job handler.

Uses streaming pipeline for 6x faster ingestion with progressive results.
"""

import logging
import os
from typing import Dict, List

import config
from api.dependencies import get_duckdb_service, get_qdrant_service, qdrant_init_error
from api.progress import progress_manager
from domain.pipeline.streaming_pipeline import StreamingPipeline
from clients.qdrant.indexing.points import PointFactory

logger = logging.getLogger(__name__)


class CancellationError(Exception):
    """Raised when a job is cancelled mid-flight."""


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

        duckdb_svc = get_duckdb_service()

        # Create image storage handler for streaming pipeline
        from domain.pipeline.storage import ImageStorageHandler
        from domain.pipeline.image_processor import ImageProcessor

        image_processor = ImageProcessor(
            default_format=config.IMAGE_FORMAT,
            default_quality=config.IMAGE_QUALITY,
        )
        image_store = ImageStorageHandler(
            minio_service=qdrant_svc.minio_service,
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
            batch_size=int(config.BATCH_SIZE),
            max_queue_size=8,
        )

        logger.info(f"Job {job_id}: Using streaming pipeline")

        # Create cancellation check function
        def check_cancellation():
            if progress_manager.is_cancelled(job_id):
                raise CancellationError("Job cancelled during processing")

        # Process each PDF
        total_pages_all = 0
        pages_processed = 0
        document_metadata_list = []

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

            logger.info(f"Starting streaming ingestion for: {filename}")

            progress_manager.update(
                job_id,
                current=pages_processed,
                message=f"Processing {filename}...",
            )

            # Get PDF info for DuckDB
            from pdf2image import pdfinfo_from_path

            try:
                info = pdfinfo_from_path(pdf_path)
                total_pages = int(info.get("Pages", 0))
                file_size_bytes = os.path.getsize(pdf_path)

                # Store metadata in DuckDB before processing
                if duckdb_svc and duckdb_svc.is_enabled():
                    from uuid import uuid4

                    document_id = str(uuid4())
                    doc_metadata = {
                        "document_id": document_id,
                        "filename": filename,
                        "file_size_bytes": file_size_bytes,
                        "total_pages": total_pages,
                    }
                    document_metadata_list.append(doc_metadata)

            except Exception as exc:
                logger.warning(f"Failed to get PDF metadata for {filename}: {exc}")
                total_pages = 0

            total_pages_all += total_pages

            # Update progress manager with total
            if progress_manager.get(job_id):
                progress_manager.set_total(job_id, total_pages_all)

            # Process PDF through streaming pipeline
            try:
                pages_in_doc = pipeline.process_pdf(
                    pdf_path=pdf_path,
                    filename=filename,
                    cancellation_check=check_cancellation,
                )

                logger.info(
                    f"Streaming ingestion complete for {filename}: {pages_in_doc} pages"
                )

            except CancellationError:
                raise
            except Exception as exc:
                logger.error(
                    f"Failed to process {filename}: {exc}",
                    exc_info=True,
                )
                raise

        # Store document metadata in DuckDB
        if duckdb_svc and duckdb_svc.is_enabled() and document_metadata_list:
            try:
                result = duckdb_svc.store_documents_batch(document_metadata_list)
                success_count = result.get("success_count", 0)
                if success_count > 0:
                    logger.info(
                        f"Stored {success_count} document metadata records in DuckDB"
                    )
            except Exception as exc:
                logger.warning(f"Failed to store document metadata in DuckDB: {exc}")

        # Wait for pipeline to finish processing all batches
        progress_manager.update(
            job_id,
            current=pages_processed,
            message="Finalizing processing...",
        )

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


__all__ = [
    "CancellationError",
    "cleanup_temp_files",
    "run_indexing_job",
]
