"""Upsert coordination stage for streaming pipeline."""

import logging
import queue
import threading
from typing import Any, Dict, List

from ..streaming_types import EmbeddedBatch
from ..utils import log_stage_timing

logger = logging.getLogger(__name__)


class UpsertStage:
    """
    Upserts embeddings to Qdrant with inline data from storage and OCR stages.

    Storage and OCR run independently and populate shared state dicts.
    Upsert reads from these dicts when building points.
    """

    def __init__(
        self,
        point_factory,
        qdrant_service,
        collection_name: str,
        shared_image_records: Dict[str, List[Dict[str, Any]]],
        shared_ocr_results: Dict[str, List[Dict[str, Any]]],
        completion_tracker=None,
    ):
        self.point_factory = point_factory
        self.qdrant_service = qdrant_service
        self.collection_name = collection_name
        self.shared_image_records = shared_image_records
        self.shared_ocr_results = shared_ocr_results
        self.completion_tracker = completion_tracker

    @log_stage_timing("Upsert")
    def process_batch(self, embedded_batch: EmbeddedBatch):
        """Build points from embeddings and upsert to Qdrant.

        Reads inline data from shared state populated by storage and OCR stages.
        """
        # Build batch key for lookup
        batch_key = f"{embedded_batch.document_id}:{embedded_batch.batch_id}"

        # Wait for storage data (with timeout)
        max_wait = 30  # seconds
        wait_interval = 0.1
        total_wait = 0

        while batch_key not in self.shared_image_records and total_wait < max_wait:
            threading.Event().wait(wait_interval)
            total_wait += wait_interval

        if batch_key not in self.shared_image_records:
            raise RuntimeError(
                f"Timeout waiting for image records for batch {batch_key}"
            )

        # Get inline image data from shared state
        image_records = self.shared_image_records.get(batch_key, [])

        # Get inline OCR data from shared state (optional)
        ocr_results = self.shared_ocr_results.get(batch_key, [])

        # Build Qdrant points with inline data
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

        # Upsert to Qdrant
        num_points = len(points)
        logger.debug("Upserting %d points to Qdrant", num_points)

        self.qdrant_service.upsert(
            collection_name=self.collection_name,
            points=points,
        )

        # Clean up shared state for this batch
        if batch_key in self.shared_image_records:
            del self.shared_image_records[batch_key]
        if batch_key in self.shared_ocr_results:
            del self.shared_ocr_results[batch_key]

        # Notify completion tracker that upsert is done for this batch
        if self.completion_tracker:
            self.completion_tracker.mark_stage_complete(
                embedded_batch.document_id, embedded_batch.batch_id, num_points
            )

    def run(
        self,
        input_queue: queue.Queue,
        stop_event: threading.Event,
    ):
        """Consumer loop: wait for embeddings and upsert."""
        logger.debug("Upsert stage started")

        while not stop_event.is_set():
            try:
                embedded_batch = input_queue.get(timeout=0.5)
            except queue.Empty:
                continue

            try:
                self.process_batch(embedded_batch)
                logger.debug("Upserted batch %d", embedded_batch.batch_id)
            except Exception as exc:
                logger.error(
                    "Upsert failed for batch %d: %s",
                    embedded_batch.batch_id,
                    exc,
                    exc_info=True,
                )
                raise
            finally:
                input_queue.task_done()

        logger.info("Upsert stage stopped")
