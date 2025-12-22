"""OCR processing stage for streaming pipeline."""

import logging
import queue
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict

import config

from ..streaming_types import PageBatch
from ..utils import log_stage_timing

logger = logging.getLogger(__name__)


class OCRStage:
    """Processes OCR independently and stores results."""

    def __init__(self, ocr_service, image_processor, qdrant_service=None, collection_name=None):
        self.ocr_service = ocr_service
        self.image_processor = image_processor
        self.qdrant_service = qdrant_service
        self.collection_name = collection_name
        # Track completion status (OCR data stored in local storage, not cached here)
        self.completed_batches: set[str] = set()  # batch_key
        self._lock = threading.Lock()

    @log_stage_timing("OCR")
    def process_batch(self, batch: PageBatch):
        """Process OCR for batch.

        Parallelism is controlled by batch size - all pages in batch are processed concurrently.
        """
        if not self.ocr_service or not config.DEEPSEEK_OCR_ENABLED:
            logger.debug("OCR skipped for batch %d (OCR disabled)", batch.batch_id)
            return

        # Process images (format conversion)
        processed_images = self.image_processor.process_batch(batch.images)

        # Process all pages in batch in parallel (batch size controls parallelism)
        num_workers = len(processed_images)
        ocr_results = [None] * num_workers

        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = {
                executor.submit(
                    self._process_single_ocr,
                    processed_images[idx],
                    batch.metadata[idx],
                ): idx
                for idx in range(len(processed_images))
            }

            for future in as_completed(futures):
                idx = futures[future]
                result = future.result()  # Will raise if OCR/storage failed
                ocr_results[idx] = result

    def _process_single_ocr(self, processed_image, meta: Dict) -> Dict:
        """Process single page OCR.

        Raises on failure - no silent fallbacks.
        """
        # Extract required fields - will raise KeyError if missing
        document_id = meta["document_id"]
        filename = meta["filename"]
        page_num = meta["page_number"]
        page_id = meta["page_id"]

        extension = self.ocr_service.image_processor.get_extension(
            processed_image.format
        )

        # Run OCR with configuration defaults
        ocr_result = self.ocr_service.processor.process_single(
            image_bytes=processed_image.data,
            filename=f"{filename}/page_{page_num}.{extension}",
            include_grounding=self.ocr_service.default_include_grounding,
            include_images=self.ocr_service.default_include_images,
        )

        # Build metadata with required fields
        ocr_metadata = {
            "filename": filename,
            "document_id": document_id,
            "page_id": page_id,
            "pdf_page_index": meta.get("pdf_page_index"),
            "total_pages": meta.get("total_pages"),
            "page_width_px": processed_image.width,
            "page_height_px": processed_image.height,
            "image_url": processed_image.url if hasattr(processed_image, "url") else None,
            "image_storage": "local",
        }

        # Process extracted images and update ocr_result with image URLs
        self.ocr_service.storage.store_ocr_result(
            ocr_result=ocr_result,
            document_id=document_id,
            page_number=page_num,
            metadata=ocr_metadata,
        )

        # Update Qdrant with OCR data (text, markdown, regions with image URLs)
        if self.qdrant_service and self.collection_name:
            try:
                from qdrant_client import models

                # Find points for this page
                scroll_filter = models.Filter(
                    must=[
                        models.FieldCondition(
                            key="document_id",
                            match=models.MatchValue(value=document_id),
                        ),
                        models.FieldCondition(
                            key="page_id",
                            match=models.MatchValue(value=page_id),
                        ),
                    ]
                )

                # Get the points to update
                points, _ = self.qdrant_service.scroll(
                    collection_name=self.collection_name,
                    scroll_filter=scroll_filter,
                    limit=100,  # Should only be a few points per page
                    with_payload=False,
                    with_vectors=False,
                )

                # Update each point with full OCR data
                if points:
                    point_ids = [point.id for point in points]

                    # Build OCR payload with full content (inline only, no URL reference)
                    ocr_payload = {
                        "ocr": {
                            "text": ocr_result.get("text", ""),
                            "markdown": ocr_result.get("markdown", ""),
                            "regions": ocr_result.get("regions", []),
                        }
                    }

                    self.qdrant_service.set_payload(
                        collection_name=self.collection_name,
                        payload=ocr_payload,
                        points=point_ids,
                    )
                    logger.debug(
                        f"Updated {len(point_ids)} points with OCR data for page {page_id}"
                    )
                else:
                    logger.warning(
                        f"No Qdrant points found for page_id={page_id}, document_id={document_id}"
                    )
            except Exception as e:
                logger.warning(
                    f"Failed to update Qdrant with OCR data for page {page_id}: {e}"
                )

        return {
            "text_preview": ocr_result.get("text", "")[:200],
            "region_count": len(ocr_result.get("regions", [])),
        }


    def run(
        self,
        input_queue: queue.Queue,
        stop_event: threading.Event,
        completion_tracker=None,
    ):
        """Consumer loop: take batches and process OCR.

        OCR failures are critical - if OCR is enabled and fails, the pipeline stops.

        Args:
            input_queue: Queue to read batches from
            stop_event: Event to signal shutdown
            completion_tracker: Optional tracker to coordinate batch completion
        """
        logger.debug("OCR stage started")

        while not stop_event.is_set():
            try:
                batch = input_queue.get(timeout=0.5)
            except queue.Empty:
                continue

            try:
                self.process_batch(batch)
                logger.debug("Processed OCR for batch %d", batch.batch_id)

                # Notify completion tracker that OCR is done for this batch
                if completion_tracker:
                    num_pages = len(batch.images)
                    completion_tracker.mark_stage_complete(
                        batch.document_id, batch.batch_id, num_pages
                    )
            except Exception as exc:
                logger.error("OCR failed for batch %d: %s", batch.batch_id, exc)
                raise  # OCR failures are critical - stop the pipeline
            finally:
                input_queue.task_done()

        logger.info("OCR stage stopped")
