"""Image storage stage for streaming pipeline."""

import logging
import queue
import threading
from typing import Dict, List, Any

from ..streaming_types import PageBatch
from ..utils import log_stage_timing

logger = logging.getLogger(__name__)


class StorageStage:
    """Converts images to base64 for inline storage in Qdrant."""

    def __init__(self, image_store, shared_image_records: Dict[str, List[Dict[str, Any]]]):
        self.image_store = image_store
        self.shared_image_records = shared_image_records

    @log_stage_timing("Storage")
    def process_batch(self, batch: PageBatch) -> None:
        """Convert images to base64 and store in shared state."""
        # Convert images to base64 using image_store (now just a converter)
        image_ids, image_records, processed_images = self.image_store.store(
            batch_start=batch.page_start,
            image_batch=batch.images,
            meta_batch=batch.metadata,
            image_ids=batch.image_ids,
        )

        # Store in shared state for Upsert stage to consume
        batch_key = f"{batch.document_id}:{batch.batch_id}"
        self.shared_image_records[batch_key] = image_records

        logger.debug(f"Stored {len(image_records)} image records for batch {batch_key}")

    def run(
        self,
        input_queue: queue.Queue,
        stop_event: threading.Event,
        completion_tracker=None,
    ):
        """Consumer loop: take batches and convert images to base64.

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
                logger.debug("Processed batch %d", batch.batch_id)

                # Notify completion tracker that storage is done for this batch
                if completion_tracker:
                    num_pages = len(batch.images)
                    completion_tracker.mark_stage_complete(
                        batch.document_id, batch.batch_id, num_pages
                    )
            except Exception as exc:
                logger.error("Storage failed for batch %d: %s", batch.batch_id, exc)
                raise
            finally:
                input_queue.task_done()

        logger.info("Storage stage stopped")
