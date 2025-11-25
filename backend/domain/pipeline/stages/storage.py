"""Image storage stage for streaming pipeline."""

import logging
import queue
import threading

from ..streaming_types import PageBatch
from ..utils import log_stage_timing

logger = logging.getLogger(__name__)


class StorageStage:
    """Stores images in MinIO independently of embedding."""

    def __init__(self, image_store):
        self.image_store = image_store

    @log_stage_timing("Storage")
    def process_batch(self, batch: PageBatch) -> None:
        """Store images in MinIO."""
        # Store images using shared image_ids from PageBatch
        # This ensures storage uses the same IDs as embedding and OCR
        self.image_store.store(
            batch_start=batch.page_start,
            image_batch=batch.images,
            meta_batch=batch.metadata,
            image_ids=batch.image_ids,  # Use pre-generated IDs
        )

    def run(
        self,
        input_queue: queue.Queue,
        stop_event: threading.Event,
        completion_tracker=None,
    ):
        """Consumer loop: take batches and store images.

        Storage failures are critical - if MinIO is unavailable, the pipeline stops.

        Args:
            input_queue: Queue to read batches from
            stop_event: Event to signal shutdown
            completion_tracker: Optional tracker to coordinate batch completion
        """
        logger.debug("Storage stage started")

        while not stop_event.is_set():
            try:
                batch = input_queue.get(timeout=0.5)
            except queue.Empty:
                continue

            try:
                self.process_batch(batch)
                logger.debug("Stored batch %d", batch.batch_id)

                # Notify completion tracker that storage is done for this batch
                if completion_tracker:
                    num_pages = len(batch.images)
                    completion_tracker.mark_stage_complete(
                        batch.document_id, batch.batch_id, num_pages
                    )
            except Exception as exc:
                logger.error("Storage failed for batch %d: %s", batch.batch_id, exc)
                raise  # Storage failures are critical - stop the pipeline
            finally:
                input_queue.task_done()

        logger.info("Storage stage stopped")
