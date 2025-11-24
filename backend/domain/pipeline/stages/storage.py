"""Image storage stage for streaming pipeline."""

import logging
import queue
import threading
from typing import Dict, List, Optional

from ..streaming_types import PageBatch
from ..utils import log_stage_timing

logger = logging.getLogger(__name__)


class StorageStage:
    """Stores images in MinIO independently of embedding."""

    def __init__(self, image_store):
        self.image_store = image_store
        self.url_cache: Dict[str, List[str]] = {}  # batch_key -> urls
        self._lock = threading.Lock()

    @log_stage_timing("Storage")
    def process_batch(self, batch: PageBatch) -> List[str]:
        """Store images and return URLs."""
        logger.info(
            f"[Storage] Starting batch {batch.batch_id + 1} (pages {batch.page_start}-"
            f"{batch.page_start + len(batch.images) - 1})"
        )

        # Store images using shared image_ids from PageBatch
        # This ensures storage uses the same IDs as embedding and OCR
        image_ids, image_records, _ = self.image_store.store(
            batch_start=batch.page_start,
            image_batch=batch.images,
            meta_batch=batch.metadata,
            image_ids=batch.image_ids,  # Use pre-generated IDs
        )

        # Extract URLs
        urls = [record["image_url"] for record in image_records]

        # Cache URLs for later retrieval by upsert stage
        batch_key = f"{batch.document_id}:{batch.batch_id}"
        with self._lock:
            self.url_cache[batch_key] = urls

        return urls

    def get_urls(self, document_id: str, batch_id: int) -> Optional[List[str]]:
        """Retrieve cached URLs for a batch."""
        batch_key = f"{document_id}:{batch_id}"
        with self._lock:
            return self.url_cache.get(batch_key)

    def run(
        self,
        input_queue: queue.Queue,
        stop_event: threading.Event,
    ):
        """Consumer loop: take batches and store images."""
        logger.info("Storage stage started")

        while not stop_event.is_set():
            try:
                batch = input_queue.get(timeout=0.5)
            except queue.Empty:
                continue

            try:
                self.process_batch(batch)
                logger.debug(f"Stored batch {batch.batch_id}")
            except Exception as exc:
                logger.error(f"Storage failed for batch {batch.batch_id}: {exc}")
                # Don't raise - storage failures shouldn't kill the pipeline
            finally:
                input_queue.task_done()

        logger.info("Storage stage stopped")
