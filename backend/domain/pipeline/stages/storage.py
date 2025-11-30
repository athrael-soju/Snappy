"""Image processing stage for streaming pipeline."""

import logging
import queue
import threading
from typing import Dict, List, Optional, Tuple

from ..streaming_types import PageBatch
from ..image_processor import ProcessedImage
from ..utils import log_stage_timing

logger = logging.getLogger(__name__)


class ProcessedImageRegistry:
    """Thread-safe registry for sharing processed images between stages.

    Storage stage populates this registry, upsert stage reads from it.
    """

    def __init__(self):
        self._data: Dict[str, Tuple[List[Dict], List[ProcessedImage]]] = {}
        self._lock = threading.Lock()

    def put(
        self,
        document_id: str,
        batch_id: int,
        image_records: List[Dict],
        processed_images: List[ProcessedImage],
    ):
        """Store processed data for a batch."""
        key = f"{document_id}:{batch_id}"
        with self._lock:
            self._data[key] = (image_records, processed_images)

    def get(
        self, document_id: str, batch_id: int
    ) -> Optional[Tuple[List[Dict], List[ProcessedImage]]]:
        """Retrieve and remove processed data for a batch."""
        key = f"{document_id}:{batch_id}"
        with self._lock:
            return self._data.pop(key, None)

    def clear(self):
        """Clear all stored data."""
        with self._lock:
            self._data.clear()


class StorageStage:
    """Processes images for inline Qdrant storage.

    Generates thumbnails and base64-encoded data, stores results in a shared
    registry for the upsert stage to consume.
    """

    def __init__(self, image_store, registry: ProcessedImageRegistry):
        """Initialize storage stage.

        Args:
            image_store: ImageStorageHandler for processing images
            registry: Shared registry to store results for upsert stage
        """
        self.image_store = image_store
        self.registry = registry

    @log_stage_timing("Storage")
    def process_batch(self, batch: PageBatch) -> None:
        """Process images and store results in registry."""
        # Process images - creates thumbnails and base64 data
        image_ids, image_records, processed_images = self.image_store.store(
            batch_start=batch.page_start,
            image_batch=batch.images,
            meta_batch=batch.metadata,
            image_ids=batch.image_ids,
        )

        # Store in shared registry for upsert stage
        self.registry.put(
            batch.document_id,
            batch.batch_id,
            image_records,
            processed_images,
        )

    def run(
        self,
        input_queue: queue.Queue,
        stop_event: threading.Event,
        completion_tracker=None,
    ):
        """Consumer loop: process images and store in registry.

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
                logger.debug("Processed images for batch %d", batch.batch_id)

                # Notify completion tracker
                if completion_tracker:
                    num_pages = len(batch.images)
                    completion_tracker.mark_stage_complete(
                        batch.document_id, batch.batch_id, num_pages
                    )
            except Exception as exc:
                logger.error("Image processing failed for batch %d: %s", batch.batch_id, exc)
                raise
            finally:
                input_queue.task_done()

        logger.info("Storage stage stopped")
