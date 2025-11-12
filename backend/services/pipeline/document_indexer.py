"""Document indexing pipeline orchestration."""

import logging
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from typing import Callable, Iterable, Iterator, Optional

import config  # Import module for dynamic config access
from services.image_processor import ImageProcessor

from .batch_processor import BatchProcessor, ProcessedBatch
from .progress import ProgressNotifier
from .storage import ImageStorageHandler
from .utils import iter_image_batches

logger = logging.getLogger(__name__)


def _estimate_pipeline_workers() -> int:
    """Determine pipeline worker count based on config heuristics."""
    return config.get_pipeline_max_concurrency()


class DocumentIndexer:
    """Generic document indexing pipeline.

    This class orchestrates the document indexing pipeline in a way that's
    independent of any specific vector database. It handles:
    - Sequential vs pipelined processing
    - Batch processing coordination
    - Progress tracking
    - Error handling

    The actual storage of processed batches is delegated via callback.
    """

    def __init__(
        self,
        embedding_processor,
        minio_service=None,
        ocr_service=None,
    ):
        """Initialize document indexer.

        Args:
            embedding_processor: Service that generates embeddings
            minio_service: MinIO service for image storage
            ocr_service: Optional OCR service
        """
        self.embedding_processor = embedding_processor
        self.minio_service = minio_service
        self.ocr_service = ocr_service

        # Create centralized image processor with config defaults
        image_processor = ImageProcessor(
            default_format=config.IMAGE_FORMAT,
            default_quality=config.IMAGE_QUALITY,
        )

        image_store = ImageStorageHandler(minio_service, image_processor)
        self._batch_processor = BatchProcessor(
            embedding_processor=embedding_processor,
            image_store=image_store,
            ocr_service=ocr_service,
        )

    def process_single_batch(
        self,
        batch_idx: int,
        batch: list,
        total_images: int,
        progress: ProgressNotifier,
        *,
        skip_progress: bool = False,
    ) -> ProcessedBatch:
        """Process a single batch of images.

        Returns ProcessedBatch with all data needed for storage.
        """
        return self._batch_processor.process(
            batch_idx=batch_idx,
            batch=batch,
            total_images=total_images,
            progress=progress,
            skip_progress=skip_progress,
        )

    def index_documents(
        self,
        images: Iterable,
        total_images: Optional[int] = None,
        progress_cb: Optional[Callable[[int, dict | None], None]] = None,
        store_batch_cb: Optional[Callable[[ProcessedBatch], None]] = None,
    ) -> str:
        """Index documents through the pipeline.

        Args:
            images: Iterable of images or dicts with 'image' key
            total_images: Total count (required for iterators)
            progress_cb: Optional progress callback
            store_batch_cb: Callback to store each processed batch

        Returns:
            Completion message
        """
        if store_batch_cb is None:
            raise ValueError("store_batch_cb is required for index_documents")

        batch_size = int(config.BATCH_SIZE)
        progress = ProgressNotifier(progress_cb)

        if isinstance(images, list):
            total = total_images if total_images is not None else len(images)
            image_iter = iter(images)
        else:
            if total_images is None:
                raise ValueError("total_images must be provided when streaming images")
            total = total_images
            image_iter = iter(images)

        if config.ENABLE_AUTO_CONFIG_MODE and total > batch_size:
            return self._index_documents_pipelined(
                image_iter, batch_size, total, progress, store_batch_cb
            )

        return self._index_documents_sequential(
            image_iter, batch_size, total, progress, store_batch_cb
        )

    def _index_documents_sequential(
        self,
        images_iter: Iterator,
        batch_size: int,
        total_images: int,
        progress: ProgressNotifier,
        store_batch_cb: Callable[[ProcessedBatch], None],
    ) -> str:
        """Process batches sequentially."""
        completed = 0
        for batch_start, batch in iter_image_batches(images_iter, batch_size):
            processed_batch = self.process_single_batch(
                batch_idx=batch_start,
                batch=batch,
                total_images=total_images,
                progress=progress,
            )

            try:
                store_batch_cb(processed_batch)
            except Exception as exc:
                raise Exception(
                    f"Error storing batch starting at {batch_start}: {exc}"
                ) from exc

            completed += processed_batch.batch_size
            progress_value = (
                min(completed, total_images) if total_images > 0 else completed
            )
            progress.stage(
                current=progress_value,
                stage="upsert",
                batch_start=processed_batch.batch_start,
                batch_size=processed_batch.batch_size,
                total=total_images,
            )

        processed = completed if total_images <= 0 else total_images
        return self._format_completion_message(processed, pipelined=False)

    def _index_documents_pipelined(
        self,
        images_iter: Iterator,
        batch_size: int,
        total_images: int,
        progress: ProgressNotifier,
        store_batch_cb: Callable[[ProcessedBatch], None],
    ) -> str:
        """Process batches in parallel pipeline."""
        max_workers = _estimate_pipeline_workers()
        completed_count = 0
        upsert_futures = []
        batch_iterator = iter_image_batches(images_iter, batch_size)

        with ThreadPoolExecutor(
            max_workers=max_workers
        ) as process_executor, ThreadPoolExecutor(
            max_workers=max_workers
        ) as upsert_executor:
            process_futures = {}

            def submit_next_batch() -> bool:
                try:
                    batch_start, batch = next(batch_iterator)
                except StopIteration:
                    return False
                future = process_executor.submit(
                    self.process_single_batch,
                    batch_start,
                    batch,
                    total_images,
                    progress,
                    skip_progress=True,
                )
                process_futures[future] = batch_start
                return True

            for _ in range(max_workers):
                if not submit_next_batch():
                    break

            try:
                while process_futures:
                    done, _ = wait(process_futures.keys(), return_when=FIRST_COMPLETED)
                    for future in done:
                        process_futures.pop(future)
                        processed_batch = future.result()

                        upsert_future = upsert_executor.submit(
                            store_batch_cb,
                            processed_batch,
                        )
                        upsert_futures.append((upsert_future, processed_batch))

                        completed_count += processed_batch.batch_size
                        progress_value = (
                            min(completed_count, total_images)
                            if total_images > 0
                            else completed_count
                        )
                        progress.stage(
                            current=progress_value,
                            stage="processing",
                            batch_start=processed_batch.batch_start,
                            batch_size=processed_batch.batch_size,
                            total=total_images,
                        )

                        submit_next_batch()

                for upsert_future, processed_batch in upsert_futures:
                    try:
                        upsert_future.result()
                    except Exception as exc:  # pragma: no cover - defensive guard
                        raise Exception(
                            f"Storage failed for batch starting at {processed_batch.batch_start}: {exc}"
                        ) from exc

            except Exception as exc:
                if (
                    "cancelled" in str(exc).lower()
                    or exc.__class__.__name__ == "CancellationError"
                ):
                    logger.info(
                        "Cancelling remaining batches due to cancellation request"
                    )
                for future in process_futures:
                    future.cancel()
                for upsert_future, _ in upsert_futures:
                    upsert_future.cancel()
                raise

        processed = completed_count if total_images <= 0 else total_images
        return self._format_completion_message(processed, pipelined=True)

    def _format_completion_message(self, processed: int, pipelined: bool) -> str:
        """Format completion message."""
        base = f"Uploaded and processed {processed} pages"
        if pipelined:
            base += " (pipelined mode)"
        return base
