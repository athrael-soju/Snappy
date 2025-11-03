"""Batch processing helpers for Qdrant indexing."""

import logging
from dataclasses import dataclass
from typing import List, Tuple

from PIL import Image
from qdrant_client import models

from .ocr import OcrResultHandler
from .points import PointFactory
from .progress import ProgressNotifier
from .storage import ImageStorageHandler

logger = logging.getLogger(__name__)


def _split_image_batch(batch: List) -> Tuple[List[Image.Image], List[dict]]:
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
    points: List[models.PointStruct]
    batch_start: int
    batch_size: int


class BatchProcessor:
    """Coordinates embedding, storage, and point construction for a batch."""

    def __init__(
        self,
        embedding_processor,
        image_store: ImageStorageHandler,
        point_factory: PointFactory,
        ocr_handler: OcrResultHandler | None = None,
    ):
        self.embedding_processor = embedding_processor
        self.image_store = image_store
        self.point_factory = point_factory
        self.ocr_handler = ocr_handler

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
        Process a batch with unified per-page progress tracking.

        Flow:
        1. Batch embed all images (efficient)
        2. For each image: OCR + storage in parallel
        3. Build Qdrant points with all metadata
        4. Progress: "Processing X/Total pages"
        """
        batch_start = batch_idx
        image_batch, meta_batch = _split_image_batch(batch)
        current_batch_size = len(batch)

        # Step 1: Batch embedding (keeps efficiency)
        progress.check_cancel(batch_start)
        if not skip_progress:
            progress.stage(
                current=batch_start,
                stage="processing",
                batch_start=batch_start,
                batch_size=current_batch_size,
                total=total_images,
            )

        original_batch, pooled_by_rows_batch, pooled_by_columns_batch = (
            self._embed_batch(image_batch)
        )

        # Step 2: Per-page OCR + storage (parallel when possible)
        try:
            # Storage first (needed for OCR metadata)
            image_ids, image_records = self.image_store.store(batch_start, image_batch)

            # OCR processing with per-page progress updates
            if self.ocr_handler:
                try:
                    ocr_results = self.ocr_handler.process_batch(
                        batch_start=batch_start,
                        total_images=total_images,
                        image_ids=image_ids,
                        image_batch=image_batch,
                        meta_batch=meta_batch,
                        image_records=image_records,
                        progress=progress,
                        skip_progress=skip_progress,
                    )
                except Exception as exc:  # pragma: no cover - defensive guard
                    logger.warning(
                        "DeepSeek OCR batch processing failed: %s", exc, exc_info=True
                    )
                    ocr_results = None

                # Merge OCR results into metadata
                if ocr_results:
                    for meta, summary in zip(meta_batch, ocr_results):
                        if summary:
                            meta.setdefault("ocr", {}).update(summary)

            # Step 3: Build points with all metadata (embedding + OCR + storage)
            points = self.point_factory.build(
                batch_start=batch_start,
                original_batch=original_batch,
                pooled_by_rows_batch=pooled_by_rows_batch,
                pooled_by_columns_batch=pooled_by_columns_batch,
                image_ids=image_ids,
                image_records=image_records,
                meta_batch=meta_batch,
            )
        finally:
            for image in image_batch:
                close = getattr(image, "close", None)
                if callable(close):
                    try:
                        close()
                    except Exception:  # pragma: no cover - defensive guard
                        pass

        return ProcessedBatch(
            points=points,
            batch_start=batch_start,
            batch_size=current_batch_size,
        )

    def _embed_batch(self, image_batch: List[Image.Image]):
        try:
            return self.embedding_processor.embed_and_mean_pool_batch(image_batch)
        except Exception as exc:
            raise Exception(f"Error during embed: {exc}") from exc
