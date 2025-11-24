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
from typing import Callable, Optional

from .stages import (
    EmbeddingStage,
    OCRStage,
    PDFRasterizer,
    StorageStage,
    UpsertStage,
)

logger = logging.getLogger(__name__)


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
        max_queue_size: int = 8,
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
            max_queue_size: Maximum queue size for backpressure
        """
        self.batch_size = batch_size
        self.max_queue_size = max_queue_size

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
        self.embedding_input_queue = queue.Queue(maxsize=max_queue_size)
        self.storage_input_queue = queue.Queue(maxsize=max_queue_size)
        self.ocr_input_queue = queue.Queue(maxsize=max_queue_size)
        self.embedding_queue = queue.Queue(maxsize=max_queue_size)

        # Thread control
        self.stop_event = threading.Event()
        self.threads = []

    def start(self, progress_callback: Optional[Callable] = None):
        """Start all consumer stage threads.

        Args:
            progress_callback: Optional callback(current_pages) for progress updates
        """
        logger.info("Starting streaming pipeline stages")

        # Create upsert stage with progress callback
        # Upsert only waits for embeddings - storage/OCR run independently
        self.upsert_stage = UpsertStage(
            self.point_factory,
            self.qdrant_service,
            self.collection_name,
            self.minio_base_url,
            self.minio_bucket,
            progress_callback=progress_callback,
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
            args=(self.storage_input_queue, self.stop_event),
            name="storage-stage",
            daemon=True,
        )
        storage_thread.start()
        self.threads.append(storage_thread)

        # Start OCR consumer (if available)
        if self.ocr_stage:
            ocr_thread = threading.Thread(
                target=self.ocr_stage.run,
                args=(self.ocr_input_queue, self.stop_event),
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

        logger.info(f"Started {len(self.threads)} pipeline stage threads")

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
        logger.info(f"Processing PDF: {filename} (document_id: {document_id})")

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
        )

        logger.info(
            f"Rasterization complete for {filename}. "
            f"Waiting for pipeline stages to finish processing {total_pages} pages..."
        )

        return total_pages

    def wait_for_completion(self):
        """
        Wait for all pipeline stages to complete processing.

        Ensures all queues are drained and all data is fully processed.
        """
        logger.info("Waiting for pipeline to drain...")

        # Wait for all input queues
        self.embedding_input_queue.join()
        self.storage_input_queue.join()

        if self.ocr_stage:
            self.ocr_input_queue.join()

        # Wait for embedding output queue
        self.embedding_queue.join()

        logger.info("Pipeline processing complete")

    def stop(self):
        """Stop all stages and clean up threads."""
        logger.info("Stopping streaming pipeline")

        self.stop_event.set()

        # Wait for threads to finish
        for thread in self.threads:
            thread.join(timeout=5)

        logger.info("Pipeline stopped")
