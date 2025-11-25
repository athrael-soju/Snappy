"""Embedding generation stage for streaming pipeline."""

import logging
import queue
import threading

from ..streaming_types import EmbeddedBatch, PageBatch
from ..utils import log_stage_timing

logger = logging.getLogger(__name__)


class EmbeddingStage:
    """Consumes rasterized pages, generates embeddings, produces embedded batches."""

    def __init__(self, embedding_processor):
        self.embedding_processor = embedding_processor

    @log_stage_timing("Embedding")
    def process_batch(self, batch: PageBatch) -> EmbeddedBatch:
        """Generate embeddings for a batch."""
        # Generate embeddings
        original, pooled_rows, pooled_cols = (
            self.embedding_processor.embed_and_mean_pool_batch(batch.images)
        )

        # Use shared image IDs from PageBatch (generated during rasterization)
        # This ensures all stages (storage, OCR, upsert) use the same IDs
        image_ids = batch.image_ids

        return EmbeddedBatch(
            document_id=batch.document_id,
            filename=batch.filename,
            batch_id=batch.batch_id,
            page_start=batch.page_start,
            original_embeddings=original,
            pooled_by_rows=pooled_rows,
            pooled_by_columns=pooled_cols,
            image_ids=image_ids,
            metadata=batch.metadata,
        )

    def run(
        self,
        input_queue: queue.Queue,
        output_queue: queue.Queue,
        stop_event: threading.Event,
    ):
        """Consumer loop: take from input, embed, push to output."""
        logger.debug("Embedding stage started")

        while not stop_event.is_set():
            try:
                # Get next batch with timeout to check stop_event
                batch = input_queue.get(timeout=0.5)
            except queue.Empty:
                continue

            try:
                embedded_batch = self.process_batch(batch)
                output_queue.put(embedded_batch, block=True)
                logger.debug("Embedded batch %d pushed to queue", batch.batch_id)
            except Exception as exc:
                logger.error("Embedding failed for batch %d: %s", batch.batch_id, exc)
                raise
            finally:
                input_queue.task_done()

        logger.info("Embedding stage stopped")
