"""Upsert coordination stage for streaming pipeline."""

import logging
import queue
import threading
import time
from typing import TYPE_CHECKING, List, Dict, Optional

from ..streaming_types import EmbeddedBatch
from ..utils import log_stage_timing

if TYPE_CHECKING:
    from .storage import ProcessedImageRegistry
    from .ocr import OcrResultRegistry

logger = logging.getLogger(__name__)

# Maximum wait time for processing to complete (seconds)
MAX_WAIT_TIME = 30
POLL_INTERVAL = 0.1


class UpsertStage:
    """
    Upserts embeddings to Qdrant with inline image and OCR data.

    Retrieves processed images and OCR results from shared registries
    and includes all data directly in the Qdrant payload.
    """

    def __init__(
        self,
        point_factory,
        qdrant_service,
        collection_name: str,
        image_registry: Optional["ProcessedImageRegistry"] = None,
        ocr_registry: Optional["OcrResultRegistry"] = None,
        completion_tracker=None,
    ):
        """Initialize upsert stage.

        Args:
            point_factory: Factory for creating Qdrant points
            qdrant_service: Qdrant client for upserting
            collection_name: Target collection name
            image_registry: Shared registry for retrieving processed images
            ocr_registry: Shared registry for retrieving OCR results
            completion_tracker: Optional tracker to coordinate batch completion
        """
        self.point_factory = point_factory
        self.qdrant_service = qdrant_service
        self.collection_name = collection_name
        self.image_registry = image_registry
        self.ocr_registry = ocr_registry
        self.completion_tracker = completion_tracker

    def _wait_for_image_records(
        self, document_id: str, batch_id: int
    ) -> Optional[List[Dict]]:
        """Wait for image processing to complete and return records.

        Polls the registry until data is available or timeout is reached.
        """
        if not self.image_registry:
            logger.warning("No image registry configured - images won't be stored inline")
            return None

        start_time = time.time()
        while time.time() - start_time < MAX_WAIT_TIME:
            result = self.image_registry.get(document_id, batch_id)
            if result is not None:
                image_records, _ = result
                return image_records
            time.sleep(POLL_INTERVAL)

        logger.error(
            f"Timeout waiting for image processing: document={document_id}, batch={batch_id}"
        )
        return None

    def _wait_for_ocr_results(
        self, document_id: str, batch_id: int
    ) -> Optional[List[Dict]]:
        """Wait for OCR processing to complete and return results.

        Polls the registry until data is available or timeout is reached.
        """
        if not self.ocr_registry:
            # OCR registry not configured - return empty results
            return None

        start_time = time.time()
        while time.time() - start_time < MAX_WAIT_TIME:
            result = self.ocr_registry.get(document_id, batch_id)
            if result is not None:
                return result
            time.sleep(POLL_INTERVAL)

        logger.warning(
            f"Timeout waiting for OCR processing: document={document_id}, batch={batch_id}"
        )
        return None

    @log_stage_timing("Upsert")
    def process_batch(self, embedded_batch: EmbeddedBatch):
        """Build points from embeddings and upsert to Qdrant.

        Waits for image and OCR processing to complete before building points.
        """
        # Wait for image processing to complete
        image_records = self._wait_for_image_records(
            embedded_batch.document_id, embedded_batch.batch_id
        )

        if image_records is None:
            # Fallback: create minimal records without inline images
            logger.warning(
                f"Using fallback records without inline images for batch {embedded_batch.batch_id}"
            )
            image_records = [
                {
                    "page_id": image_id,
                    "image_inline": False,
                    "image_storage": "none",
                }
                for image_id in embedded_batch.image_ids
            ]

        # Wait for OCR processing to complete (if registry is configured)
        ocr_results = self._wait_for_ocr_results(
            embedded_batch.document_id, embedded_batch.batch_id
        )

        # Build Qdrant points with inline image and OCR data
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
