"""OCR processing stage for streaming pipeline."""

import logging
import queue
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Tuple

import config

from ..streaming_types import PageBatch
from ..utils import log_stage_timing

logger = logging.getLogger(__name__)


class OcrResultRegistry:
    """Thread-safe registry for sharing OCR results between stages.

    OCR stage populates this registry, upsert stage reads from it.
    """

    def __init__(self):
        self._data: Dict[str, List[Dict]] = {}
        self._lock = threading.Lock()

    def put(
        self,
        document_id: str,
        batch_id: int,
        ocr_results: List[Dict],
    ):
        """Store OCR results for a batch."""
        key = f"{document_id}:{batch_id}"
        with self._lock:
            self._data[key] = ocr_results

    def get(
        self, document_id: str, batch_id: int
    ) -> Optional[List[Dict]]:
        """Retrieve and remove OCR results for a batch."""
        key = f"{document_id}:{batch_id}"
        with self._lock:
            return self._data.pop(key, None)

    def clear(self):
        """Clear all stored data."""
        with self._lock:
            self._data.clear()


class OCRStage:
    """Processes OCR and stores results in registry for inline storage."""

    def __init__(self, ocr_service, image_processor, registry: Optional[OcrResultRegistry] = None):
        """Initialize OCR stage.

        Args:
            ocr_service: OCR service for text extraction
            image_processor: Image processor for format conversion
            registry: Shared registry to store results for upsert stage
        """
        self.ocr_service = ocr_service
        self.image_processor = image_processor
        self.registry = registry
        self._lock = threading.Lock()

    @log_stage_timing("OCR")
    def process_batch(self, batch: PageBatch):
        """Process OCR for batch.

        Parallelism is controlled by batch size - all pages in batch are processed concurrently.
        Results are stored in the shared registry for the upsert stage.
        """
        if not self.ocr_service or not config.DEEPSEEK_OCR_ENABLED:
            logger.debug("OCR skipped for batch %d (OCR disabled)", batch.batch_id)
            # Store empty results so upsert doesn't wait forever
            if self.registry:
                empty_results = [{"ocr_text": None, "ocr_markdown": None} for _ in batch.images]
                self.registry.put(batch.document_id, batch.batch_id, empty_results)
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
                result = future.result()  # Will raise if OCR failed
                ocr_results[idx] = result

        # Store results in registry for upsert stage
        if self.registry:
            self.registry.put(batch.document_id, batch.batch_id, ocr_results)

    def _process_single_ocr(self, processed_image, meta: Dict) -> Dict:
        """Process single page OCR.

        Returns inline OCR data (text, markdown) instead of URLs.
        Raises on failure - no silent fallbacks.
        """
        # Extract required fields
        filename = meta["filename"]
        page_num = meta["page_number"]

        extension = self.image_processor.get_extension(processed_image.format)

        # Run OCR with configuration defaults
        ocr_result = self.ocr_service.processor.process_single(
            image_bytes=processed_image.data,
            filename=f"{filename}/page_{page_num}.{extension}",
            include_grounding=self.ocr_service.default_include_grounding,
            include_images=self.ocr_service.default_include_images,
        )

        # Return inline OCR data
        return {
            "ocr_text": ocr_result.get("text", ""),
            "ocr_markdown": ocr_result.get("markdown", ""),
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
