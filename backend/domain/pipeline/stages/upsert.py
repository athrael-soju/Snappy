"""Upsert coordination stage for streaming pipeline."""

import logging
import queue
import threading
from typing import Callable, Optional

from ..streaming_types import EmbeddedBatch
from ..utils import log_stage_timing

logger = logging.getLogger(__name__)


class UpsertStage:
    """
    Coordinates final upsert by combining embeddings with storage/OCR results.

    Waits for storage and OCR to complete for each batch before upserting.
    """

    def __init__(
        self,
        point_factory,
        qdrant_service,
        collection_name: str,
        storage_stage,
        ocr_stage: Optional = None,
        progress_callback: Optional[Callable] = None,
        buffer_size: int = 4,
    ):
        self.point_factory = point_factory
        self.qdrant_service = qdrant_service
        self.collection_name = collection_name
        self.storage_stage = storage_stage
        self.ocr_stage = ocr_stage
        self.progress_callback = progress_callback
        self.upsert_buffer = []
        self.buffer_size = buffer_size  # Batch upserts (default: 4 to match batch size)
        self.pages_upserted = 0  # Track progress

    @log_stage_timing("Upsert")
    def process_batch(self, embedded_batch: EmbeddedBatch):
        """Build points and upsert to Qdrant."""
        logger.info(
            f"[Upsert] Starting batch {embedded_batch.batch_id + 1} "
            f"(pages {embedded_batch.page_start}-{embedded_batch.page_start + len(embedded_batch.original_embeddings) - 1})"
        )

        # Look up storage URLs from cache (no waiting - storage runs in parallel)
        image_urls = self.storage_stage.get_urls(
            embedded_batch.document_id,
            embedded_batch.batch_id,
        )

        if not image_urls:
            logger.warning(
                f"Storage data not available for batch {embedded_batch.batch_id + 1}, "
                "proceeding without URLs"
            )
            image_urls = [""] * len(embedded_batch.original_embeddings)

        # Look up OCR results from cache (no waiting - OCR runs in parallel)
        ocr_results = None
        if self.ocr_stage:
            ocr_results = self.ocr_stage.get_ocr_results(
                embedded_batch.document_id,
                embedded_batch.batch_id,
            )

            if not ocr_results:
                logger.warning(
                    f"OCR data not available for batch {embedded_batch.batch_id + 1}, "
                    "proceeding without OCR data"
                )

        # Build image records
        image_records = [
            {
                "image_url": url,
                "image_inline": False,
                "image_storage": "minio",
                "page_id": image_id,
            }
            for url, image_id in zip(image_urls, embedded_batch.image_ids)
        ]

        # Build Qdrant points
        points = self.point_factory.build(
            batch_start=embedded_batch.page_start,
            original_batch=embedded_batch.original_embeddings,
            pooled_by_rows_batch=embedded_batch.pooled_by_rows,
            pooled_by_columns_batch=embedded_batch.pooled_by_columns,
            image_ids=embedded_batch.image_ids,
            image_records=image_records,
            meta_batch=embedded_batch.metadata,
            ocr_results=ocr_results,
        )

        # Add to buffer
        self.upsert_buffer.extend(points)

        # Flush if buffer is full
        if len(self.upsert_buffer) >= self.buffer_size:
            self._flush()

    def _flush(self):
        """Flush accumulated points to Qdrant."""
        if not self.upsert_buffer:
            return

        num_points = len(self.upsert_buffer)
        logger.info(f"Upserting {num_points} points to Qdrant")

        self.qdrant_service.upsert(
            collection_name=self.collection_name,
            points=self.upsert_buffer,
        )

        self.upsert_buffer = []

        # Update progress AFTER successful upsert
        self.pages_upserted += num_points
        if self.progress_callback:
            try:
                self.progress_callback(self.pages_upserted)
            except Exception as exc:
                logger.warning(f"Progress callback failed: {exc}")

    def flush_remaining(self):
        """Public method to flush any remaining buffered points."""
        logger.info("Flushing remaining buffered points...")
        self._flush()

    def run(
        self,
        input_queue: queue.Queue,
        stop_event: threading.Event,
    ):
        """Consumer loop: take embedded batches and upsert."""
        logger.info("Upsert stage started")

        while not stop_event.is_set():
            try:
                embedded_batch = input_queue.get(timeout=0.5)
            except queue.Empty:
                continue

            try:
                self.process_batch(embedded_batch)
                logger.debug(f"Upserted batch {embedded_batch.batch_id}")
            except Exception as exc:
                logger.error(
                    f"Upsert failed for batch {embedded_batch.batch_id}: {exc}",
                    exc_info=True,
                )
                raise
            finally:
                input_queue.task_done()

        # Flush remaining points
        self._flush()

        logger.info("Upsert stage stopped")
