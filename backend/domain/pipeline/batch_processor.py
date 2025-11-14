"""Batch processing helpers for pipeline processing."""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import config
from PIL import Image
from utils.timing import log_execution_time

from .progress import ProgressNotifier
from .storage import ImageStorageHandler
from .image_processor import ProcessedImage

logger = logging.getLogger(__name__)


def _split_image_batch(batch: List) -> Tuple[List[Image.Image], List[dict]]:
    """Split a batch into images and metadata."""
    image_batch: List[Image.Image] = []
    meta_batch: List[dict] = []
    for item in batch:
        if isinstance(item, Image.Image):
            image_batch.append(item)
            meta_batch.append({})
        else:
            image = item.get("image")
            if image is None:
                raise ValueError("Batch item missing 'image'")
            image_batch.append(image)
            meta = {k: v for k, v in dict(item).items() if k != "image"}
            meta_batch.append(meta)
    return image_batch, meta_batch


@dataclass
class ProcessedBatch:
    """Result of processing a batch of images."""

    batch_start: int
    batch_size: int
    original_embeddings: List
    pooled_by_rows: Optional[List]
    pooled_by_columns: Optional[List]
    image_ids: List[str]
    image_records: List[Dict[str, object]]
    meta_batch: List[dict]
    ocr_results: Optional[List[Dict]]


class BatchProcessor:
    """Coordinates embedding, storage, and OCR for a batch of images.

    This is a vector-database-agnostic batch processor that handles:
    - Embedding generation
    - Image storage
    - OCR processing (optional)
    - Progress notifications

    The actual point/document construction is delegated to the caller.
    """

    def __init__(
        self,
        embedding_processor,
        image_store: ImageStorageHandler,
        ocr_service=None,
        job_id: str | None = None,
    ):
        """Initialize batch processor.

        Args:
            embedding_processor: Service that generates embeddings
            image_store: Handler for image storage
            ocr_service: Optional OCR service for text extraction
            job_id: Optional job ID for tracking and cancellation
        """
        self.embedding_processor = embedding_processor
        self.image_store = image_store
        self.ocr_service = ocr_service
        self.job_id = job_id

    def process(
        self,
        batch_idx: int,
        batch: List,
        total_images: int,
        progress: ProgressNotifier,
        *,
        skip_progress: bool = False,
    ) -> ProcessedBatch:
        """
        Process a batch with embedding, storage, and optional OCR in parallel.

        Flow:
        1. Batch embed all images (efficient)
        2. Process images (format/quality conversion)
        3. In parallel:
           - Store images to MinIO
           - Run OCR if service is available (non-blocking)
        4. Return processed batch data for point construction
        5. Progress: "Processing X/Total pages"

        Args:
            batch_idx: Starting index of this batch
            batch: List of images or dicts with 'image' key
            total_images: Total number of images being processed
            progress: Progress notifier
            skip_progress: Whether to skip progress updates

        Returns:
            ProcessedBatch with all data needed for point construction
        """
        batch_start = batch_idx
        image_batch, meta_batch = _split_image_batch(batch)
        current_batch_size = len(batch)

        # Step 1: Check cancellation before any processing
        progress.check_cancel(batch_start)
        if not skip_progress:
            progress.stage(
                current=batch_start,
                stage="processing",
                batch_start=batch_start,
                batch_size=current_batch_size,
                total=total_images,
            )

        # Step 2: Batch embedding (check cancellation before expensive operation)
        progress.check_cancel(batch_start)
        original_batch, pooled_by_rows_batch, pooled_by_columns_batch = (
            self._embed_batch(image_batch)
        )

        # Step 3: Storage and optional OCR in parallel (check before storage)
        progress.check_cancel(batch_start)
        try:
            image_ids, image_records, processed_images = self.image_store.store(
                batch_start, image_batch, meta_batch
            )

            # Step 3: Run OCR in parallel if enabled (non-blocking)
            ocr_results: Optional[List[Dict]] = None
            if self.ocr_service is not None and config.DEEPSEEK_OCR_ENABLED:
                try:
                    logger.debug(
                        f"Starting parallel OCR processing for batch {batch_start}"
                    )
                    raw_ocr_results = self._process_ocr_batch(
                        processed_images, meta_batch
                    )
                    if raw_ocr_results:
                        # Filter out None values for type safety
                        ocr_results = [r for r in raw_ocr_results if r is not None]
                        if len(ocr_results) != len(raw_ocr_results):
                            logger.warning(
                                f"OCR had {len(raw_ocr_results) - len(ocr_results)} failures"
                            )
                except Exception as exc:
                    logger.exception(f"ocr processing failed: {exc}")
                    # Continue without OCR results

        finally:
            for image in image_batch:
                close = getattr(image, "close", None)
                if callable(close):
                    try:
                        close()
                    except Exception:  # pragma: no cover - defensive guard
                        pass

        return ProcessedBatch(
            batch_start=batch_start,
            batch_size=current_batch_size,
            original_embeddings=original_batch,
            pooled_by_rows=pooled_by_rows_batch,
            pooled_by_columns=pooled_by_columns_batch,
            image_ids=image_ids,
            image_records=image_records,
            meta_batch=meta_batch,
            ocr_results=ocr_results,
        )

    def _embed_batch(self, image_batch: List[Image.Image]):
        """Generate embeddings for a batch of images."""
        try:
            return self.embedding_processor.embed_and_mean_pool_batch(image_batch)
        except Exception as exc:
            raise Exception(f"Error during embed: {exc}") from exc

    @log_execution_time(
        "ocr processing", log_level=logging.INFO, warn_threshold_ms=10000
    )
    def _process_ocr_batch(
        self, processed_images: List[ProcessedImage], meta_batch: List[dict]
    ) -> Optional[List[Optional[dict]]]:
        """
        Process OCR for a batch of images in parallel (non-blocking).

        Returns list of OCR results (or None for each image if OCR disabled/fails).
        Does not raise exceptions - logs and continues on failure.
        """
        if not self.ocr_service or not self.ocr_service.is_enabled():
            return None

        if not processed_images:
            return None

        if len(processed_images) != len(meta_batch):
            logger.warning(
                "Processed images and metadata length mismatch: %s vs %s",
                len(processed_images),
                len(meta_batch),
            )

        effective_length = min(len(processed_images), len(meta_batch))
        ocr_results: List[Optional[dict]] = [None] * effective_length

        try:
            import config

            max_workers = getattr(config, "DEEPSEEK_OCR_MAX_WORKERS", 4)
            max_workers = max(1, min(max_workers, effective_length))

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {
                    executor.submit(self._process_single_ocr, img, meta): idx
                    for idx, (img, meta) in enumerate(
                        zip(
                            processed_images[:effective_length],
                            meta_batch[:effective_length],
                        )
                    )
                }

                for future in as_completed(futures):
                    idx = futures[future]
                    try:
                        result = future.result()
                        ocr_results[idx] = result
                    except Exception as exc:
                        logger.warning(f"OCR failed for image {idx} in batch: {exc}")
                        ocr_results[idx] = None

        except Exception as exc:
            logger.warning(f"ocr processing error: {exc}")
            return None

        return ocr_results

    def _process_single_ocr(
        self, processed_image: ProcessedImage, meta: dict
    ) -> Optional[dict]:
        """Process a single image with OCR."""
        if self.ocr_service is None:
            return None

        try:
            # Get filename and page for naming
            filename = meta.get("filename", "unknown")
            page_num = meta.get("page_number", 0)
            extension = self.ocr_service.image_processor.get_extension(
                processed_image.format
            )

            # Run OCR
            ocr_result = self.ocr_service.processor.process_single(
                image_bytes=processed_image.data,
                filename=f"{filename}/page_{page_num}.{extension}",
            )

            # Build metadata for storage
            ocr_metadata = {
                "page_width_px": processed_image.width,
                "page_height_px": processed_image.height,
                "image_url": processed_image.url,
                "image_storage": "minio",
            }

            # Store OCR results with metadata
            # Returns: {"ocr_url": "...", "ocr_regions": [{"label": "...", "url": "...", "id": "..."}]}
            storage_result = self.ocr_service.storage.store_ocr_result(
                ocr_result=ocr_result,
                filename=filename,
                page_number=page_num,
                metadata=ocr_metadata,
            )

            return {
                "ocr_url": storage_result.get("ocr_url"),
                "ocr_regions": storage_result.get("ocr_regions", []),
                "text_preview": ocr_result.get("text", "")[:200],
                "region_count": len(ocr_result.get("regions", [])),
            }

        except Exception as exc:
            logger.warning(f"Single OCR processing failed: {exc}")
            return None
