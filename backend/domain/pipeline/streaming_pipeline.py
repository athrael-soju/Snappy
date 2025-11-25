"""
Streaming pipeline orchestrator for PDF ingestion.

This module provides a high-level orchestrator that coordinates independent
parallel stages for PDF processing. The actual stage implementations are in
the stages/ subpackage.

Architecture:
- PDF rasterization produces pages as soon as they're ready
- Embedding, storage, and OCR run independently in parallel
- All stages coordinate via document_id:batch_id keys
- Backpressure prevents memory overflow via bounded queues

Benefits:
- First results available in ~8 seconds vs 60+ seconds
- 3-6x faster for large documents
- Better resource utilization (GPU, CPU, I/O all busy)
- Progressive user feedback (pages appear as they're processed)
"""

import logging
import queue
import threading
import time
from collections import defaultdict
from typing import Callable, Optional

from .console import get_pipeline_console
from .stages import (
    EmbeddingStage,
    OCRStage,
    PDFRasterizer,
    StorageStage,
    UpsertStage,
)

logger = logging.getLogger(__name__)


class BatchCompletionTracker:
    """Tracks completion of all stages for each batch to coordinate progress updates."""

    def __init__(
        self,
        num_stages: int,
        progress_callback: Optional[Callable] = None,
        batch_semaphore: Optional[threading.Semaphore] = None,
    ):
        """Initialize tracker.

        Args:
            num_stages: Number of parallel stages that must complete per batch
            progress_callback: Callback to invoke when all stages complete a batch
            batch_semaphore: Optional semaphore to release when batch completes
        """
        self.num_stages = num_stages
        self.progress_callback = progress_callback
        self.batch_semaphore = batch_semaphore
        self.batch_completions = defaultdict(int)  # batch_key -> completion_count
        self.completed_pages = 0
        self._lock = threading.Lock()

    def mark_stage_complete(self, document_id: str, batch_id: int, num_pages: int):
        """Mark a stage as complete for a batch.

        Args:
            document_id: Document identifier
            batch_id: Batch identifier
            num_pages: Number of pages in this batch

        When all stages complete, triggers progress callback and releases semaphore.
        """
        batch_key = f"{document_id}:{batch_id}"

        with self._lock:
            self.batch_completions[batch_key] += 1

            if self.batch_completions[batch_key] == self.num_stages:
                # All stages complete for this batch
                self.completed_pages += num_pages

                # Log batch completion with Rich console (pass batch page count)
                console = get_pipeline_console()
                console.batch_completed(batch_id, num_pages)

                # Clean up tracking for this batch
                del self.batch_completions[batch_key]

                # Release semaphore to allow next batch to enter pipeline
                if self.batch_semaphore:
                    self.batch_semaphore.release()

                # Report progress
                if self.progress_callback:
                    try:
                        self.progress_callback(self.completed_pages)
                    except Exception as exc:
                        logger.warning("Progress callback failed: %s", exc)


class StreamingPipeline:
    """
    Orchestrates the streaming PDF processing pipeline.

    Responsibilities:
    - Create and manage processing queues
    - Start and stop stage threads
    - Coordinate data flow between stages
    - Provide lifecycle management

    Does NOT contain stage logic - delegates to stage classes.
    """

    def __init__(
        self,
        embedding_processor,
        image_store,
        image_processor,
        ocr_service,
        point_factory,
        qdrant_service,
        collection_name: str,
        minio_base_url: str,
        minio_bucket: str,
        batch_size: int = 4,
        max_in_flight_batches: int = 1,
    ):
        """Initialize streaming pipeline with all dependencies injected.

        Args:
            embedding_processor: Service for generating embeddings
            image_store: Handler for image storage
            image_processor: Processor for image format conversion
            ocr_service: Optional OCR service
            point_factory: Factory for creating Qdrant points
            qdrant_service: Qdrant client for vector storage
            collection_name: Target Qdrant collection
            minio_base_url: MinIO base URL for generating dynamic URLs
            minio_bucket: MinIO bucket name
            batch_size: Number of pages per batch
            max_in_flight_batches: Maximum batches processing simultaneously
        """
        self.batch_size = batch_size
        self.max_in_flight_batches = max_in_flight_batches

        # Derive queue size from in-flight batches (allow some buffering)
        self.max_queue_size = max(2, max_in_flight_batches * 2)

        # Create stages with injected dependencies
        self.rasterizer = PDFRasterizer(batch_size=batch_size)
        self.embedding_stage = EmbeddingStage(embedding_processor)
        self.storage_stage = StorageStage(image_store)
        self.ocr_stage = OCRStage(ocr_service, image_processor) if ocr_service else None
        self.upsert_stage = None  # Created in start() with progress callback

        # Store dependencies for upsert stage creation
        self.point_factory = point_factory
        self.qdrant_service = qdrant_service
        self.collection_name = collection_name
        self.minio_base_url = minio_base_url
        self.minio_bucket = minio_bucket

        # Create bounded queues for backpressure control
        self.embedding_input_queue = queue.Queue(maxsize=self.max_queue_size)
        self.storage_input_queue = queue.Queue(maxsize=self.max_queue_size)
        self.ocr_input_queue = queue.Queue(maxsize=self.max_queue_size)
        self.embedding_queue = queue.Queue(maxsize=self.max_queue_size)

        # Thread control
        self.stop_event = threading.Event()
        self.threads = []

        # Batch completion tracker (created in start())
        self.completion_tracker = None

    def start(self, progress_callback: Optional[Callable] = None):
        """Start all consumer stage threads.

        Args:
            progress_callback: Optional callback(current_pages) for progress updates
        """
        logger.info("Starting streaming pipeline stages")

        # Count active stages (embedding + storage + optional OCR)
        # Embedding stage doesn't count because it only produces, doesn't complete
        # We only count stages that perform final work: storage, OCR, upsert
        num_stages = 2  # storage + upsert
        if self.ocr_stage:
            num_stages += 1  # + ocr

        # Create semaphore to limit in-flight batches
        batch_semaphore = threading.Semaphore(self.max_in_flight_batches)

        # Create batch completion tracker with semaphore
        self.completion_tracker = BatchCompletionTracker(
            num_stages=num_stages,
            progress_callback=progress_callback,
            batch_semaphore=batch_semaphore,
        )

        # Store semaphore for rasterizer to use
        self.batch_semaphore = batch_semaphore

        # Create upsert stage with completion tracker instead of direct callback
        self.upsert_stage = UpsertStage(
            self.point_factory,
            self.qdrant_service,
            self.collection_name,
            self.minio_base_url,
            self.minio_bucket,
            completion_tracker=self.completion_tracker,
        )

        # Start embedding consumer
        embedding_thread = threading.Thread(
            target=self.embedding_stage.run,
            args=(self.embedding_input_queue, self.embedding_queue, self.stop_event),
            name="embedding-stage",
            daemon=True,
        )
        embedding_thread.start()
        self.threads.append(embedding_thread)

        # Start storage consumer
        storage_thread = threading.Thread(
            target=self.storage_stage.run,
            args=(self.storage_input_queue, self.stop_event, self.completion_tracker),
            name="storage-stage",
            daemon=True,
        )
        storage_thread.start()
        self.threads.append(storage_thread)

        # Start OCR consumer (if available)
        if self.ocr_stage:
            ocr_thread = threading.Thread(
                target=self.ocr_stage.run,
                args=(self.ocr_input_queue, self.stop_event, self.completion_tracker),
                name="ocr-stage",
                daemon=True,
            )
            ocr_thread.start()
            self.threads.append(ocr_thread)

        # Start upsert consumer
        upsert_thread = threading.Thread(
            target=self.upsert_stage.run,
            args=(self.embedding_queue, self.stop_event),
            name="upsert-stage",
            daemon=True,
        )
        upsert_thread.start()
        self.threads.append(upsert_thread)

        logger.debug("Started %d pipeline stage threads", len(self.threads))

    def process_pdf(
        self,
        pdf_path: str,
        filename: str,
        document_id: str,
        cancellation_check: Optional[Callable] = None,
    ) -> int:
        """
        Process a PDF through the streaming pipeline.

        Args:
            pdf_path: Path to PDF file
            filename: Display name for the document
            document_id: Unique document identifier (provided by caller)
            cancellation_check: Optional function to check for cancellation

        Returns:
            Total pages processed
        """
        self._start_time = time.time()
        self._current_filename = filename
        logger.debug("Processing PDF: %s (document_id: %s)", filename, document_id)

        # Build list of output queues for broadcasting
        output_queues = [self.embedding_input_queue, self.storage_input_queue]
        if self.ocr_stage:
            output_queues.append(self.ocr_input_queue)

        # Rasterize and broadcast to all queues
        total_pages = self.rasterizer.rasterize_streaming(
            pdf_path=pdf_path,
            filename=filename,
            document_id=document_id,
            output_queues=output_queues,
            cancellation_check=cancellation_check,
            batch_semaphore=self.batch_semaphore,
        )

        logger.debug(
            "Rasterization complete for %s. Waiting for %d pages to finish processing...",
            filename,
            total_pages,
        )

        return total_pages

    def wait_for_completion(self):
        """
        Wait for all pipeline stages to complete processing.

        Ensures all queues are drained and all data is fully processed.
        """
        logger.debug("Waiting for pipeline to drain...")

        # Wait for all input queues
        self.embedding_input_queue.join()
        self.storage_input_queue.join()

        if self.ocr_stage:
            self.ocr_input_queue.join()

        # Wait for embedding output queue
        self.embedding_queue.join()

        # Print completion summary with Rich console
        if hasattr(self, "_start_time") and self.completion_tracker:
            total_time = time.time() - self._start_time
            total_pages = self.completion_tracker.completed_pages
            console = get_pipeline_console()
            console.document_completed(total_pages, total_time)

        logger.debug("Pipeline processing complete")

    def stop(self):
        """Stop all stages and clean up threads."""
        logger.info("Stopping streaming pipeline")

        self.stop_event.set()

        # Wait for threads to finish
        for thread in self.threads:
            thread.join(timeout=5)

        logger.info("Pipeline stopped")
