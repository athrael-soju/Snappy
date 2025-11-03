"""Document indexing operations for Qdrant."""

import logging
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from typing import Callable, Iterable, Iterator, Optional

import config  # Import module for dynamic config access

from .ocr import OcrResultHandler
from .points import PointFactory
from .processor import BatchProcessor, ProcessedBatch
from .progress import ProgressNotifier
from .storage import ImageStorageHandler
from .utils import iter_image_batches

logger = logging.getLogger(__name__)


def _estimate_pipeline_workers() -> int:
    """Determine pipeline worker count based on config heuristics."""
    return config.get_pipeline_max_concurrency()


class DocumentIndexer:
    """Handles document indexing operations."""

    def __init__(
        self,
        qdrant_client,
        collection_name: str,
        embedding_processor,
        minio_service=None,
        muvera_post=None,
        deepseek_service=None,
    ):
        """Initialize document indexer."""
        self.service = qdrant_client
        self.collection_name = collection_name
        self.embedding_processor = embedding_processor
        self.minio_service = minio_service
        self.muvera_post = muvera_post
        self.ocr_handler = None

        if deepseek_service and minio_service:
            try:
                if deepseek_service.is_enabled():
                    self.ocr_handler = OcrResultHandler(
                        ocr_service=deepseek_service,
                        minio_service=minio_service,
                    )
            except Exception as exc:  # pragma: no cover - defensive guard
                logger.warning("DeepSeek OCR handler disabled: %s", exc)

        image_store = ImageStorageHandler(minio_service)
        point_factory = PointFactory(muvera_post)
        self._batch_processor = BatchProcessor(
            embedding_processor=embedding_processor,
            image_store=image_store,
            point_factory=point_factory,
            ocr_handler=self.ocr_handler,
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
    ) -> str:
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

        if config.ENABLE_PIPELINE_INDEXING and total > batch_size:
            return self._index_documents_pipelined(
                image_iter, batch_size, total, progress
            )

        return self._index_documents_sequential(image_iter, batch_size, total, progress)

    def _index_documents_sequential(
        self,
        images_iter: Iterator,
        batch_size: int,
        total_images: int,
        progress: ProgressNotifier,
    ) -> str:
        completed = 0
        for batch_start, batch in iter_image_batches(images_iter, batch_size):
            processed_batch = self.process_single_batch(
                batch_idx=batch_start,
                batch=batch,
                total_images=total_images,
                progress=progress,
            )

            try:
                self.service.upsert(
                    collection_name=self.collection_name,
                    points=processed_batch.points,
                )
            except Exception as exc:
                raise Exception(
                    f"Error during upsert for batch starting at {batch_start}: {exc}"
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
    ) -> str:
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
                            self.service.upsert,
                            collection_name=self.collection_name,
                            points=processed_batch.points,
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
                            f"Upsert failed for batch starting at {processed_batch.batch_start}: {exc}"
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
        base = f"Uploaded and processed {processed} pages"
        if self.ocr_handler:
            base += " with DeepSeek OCR"
        if pipelined:
            base += " (pipelined mode)"
        return base
