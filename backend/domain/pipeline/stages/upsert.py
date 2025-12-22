"""Upsert coordination stage for streaming pipeline."""

import logging
import queue
import threading
import config
from ..streaming_types import EmbeddedBatch
from ..utils import log_stage_timing

logger = logging.getLogger(__name__)


class UpsertStage:
    """
    Upserts embeddings to Qdrant with dynamically generated URLs.

    Storage and OCR run independently - UpsertStage only waits for embeddings.
    URLs are generated on-the-fly from metadata (no coordination needed).
    """

    def __init__(
        self,
        point_factory,
        qdrant_service,
        collection_name: str,
        storage_base_url: str,
        storage_bucket: str,
        completion_tracker=None,
    ):
        self.point_factory = point_factory
        self.qdrant_service = qdrant_service
        self.collection_name = collection_name
        self.storage_base_url = storage_base_url
        self.storage_bucket = storage_bucket
        self.completion_tracker = completion_tracker

    def _generate_image_url(self, document_id: str, page_number: int, page_id: str) -> str:
        """Generate storage image URL from metadata.

        Pattern: {storage_base_url}/{bucket}/{doc_id}/{page_num}/image/{page_id}.{ext}
        """
        fmt = config.IMAGE_FORMAT.lower()
        ext = "jpg" if fmt == "jpeg" else fmt
        object_name = f"{document_id}/{page_number}/image/{page_id}.{ext}"

        base = self.storage_base_url.rstrip("/")
        bucket_suffix = f"/{self.storage_bucket}" if self.storage_bucket else ""
        return f"{base}{bucket_suffix}/{object_name}"

    @log_stage_timing("Upsert")
    def process_batch(self, embedded_batch: EmbeddedBatch):
        """Build points from embeddings and upsert to Qdrant.

        Storage/OCR run independently - we just generate URL references.
        """
        # Generate image URLs dynamically - storage runs independently
        image_urls = []

        for idx, (page_id, meta) in enumerate(zip(embedded_batch.image_ids, embedded_batch.metadata)):
            page_number = meta.get("page_number", embedded_batch.page_start + idx)

            image_urls.append(
                self._generate_image_url(embedded_batch.document_id, page_number, page_id)
            )

        # Build image records
        image_records = [
            {
                "image_url": url,
                "image_inline": False,
                "image_storage": "local",
                "page_id": image_id,
            }
            for url, image_id in zip(image_urls, embedded_batch.image_ids)
        ]

        # Build Qdrant points (OCR data added separately by OCR stage)
        points = self.point_factory.build(
            batch_start=embedded_batch.page_start,
            original_batch=embedded_batch.original_embeddings,
            pooled_by_rows_batch=embedded_batch.pooled_by_rows,
            pooled_by_columns_batch=embedded_batch.pooled_by_columns,
            image_ids=embedded_batch.image_ids,
            image_records=image_records,
            meta_batch=embedded_batch.metadata,
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
