"""Document indexing operations for Qdrant."""

import uuid
import logging
from datetime import datetime
from itertools import islice
from typing import Callable, Iterable, Iterator, List, Optional, Tuple
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait

from PIL import Image
from qdrant_client import models

import config  # Import module for dynamic config access

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
    ):
        """Initialize document indexer."""
        self.service = qdrant_client
        self.collection_name = collection_name
        self.embedding_processor = embedding_processor
        self.minio_service = minio_service
        self.muvera_post = muvera_post

    @staticmethod
    def _call_progress(
        progress_cb: Optional[Callable[[int, dict | None], None]],
        current: int,
        info: Optional[dict],
        *,
        skip_updates: bool = False,
    ) -> None:
        if not progress_cb:
            return
        if skip_updates and info and info.get("stage") != "check_cancel":
            return
        try:
            progress_cb(current, info)
        except Exception as exc:  # pragma: no cover - defensive guard
            if "cancelled" in str(exc).lower() or exc.__class__.__name__ == "CancellationError":
                raise
            logger.debug("Progress callback raised %s (ignored)", exc)

    @staticmethod
    def _split_batch(batch: List) -> Tuple[List[Image.Image], List[dict]]:
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

    @staticmethod
    def _batch_iterator(images_iter: Iterator, batch_size: int):
        batch_start = 0
        while True:
            batch = list(islice(images_iter, batch_size))
            if not batch:
                break
            yield batch_start, batch
            batch_start += len(batch)

    def _embed_batch(self, image_batch: List[Image.Image]):
        try:
            return self.embedding_processor.embed_and_mean_pool_batch(image_batch)
        except Exception as exc:
            raise Exception(f"Error during embed: {exc}") from exc

    def _store_images(
        self,
        batch_start: int,
        image_batch: List[Image.Image],
    ) -> Tuple[List[str], List[str]]:
        if not self.minio_service:
            raise Exception("MinIO service not available")

        image_ids = [str(uuid.uuid4()) for _ in image_batch]
        try:
            image_url_map = self.minio_service.store_images_batch(
                image_batch,
                image_ids=image_ids,
                quality=config.MINIO_IMAGE_QUALITY,
            )
        except Exception as exc:
            raise Exception(
                f"Error storing images in MinIO for batch starting at {batch_start}: {exc}"
            ) from exc

        image_urls = [image_url_map.get(image_id) for image_id in image_ids]
        if any(url is None for url in image_urls):
            raise Exception(
                f"Image upload failed for batch starting at {batch_start}: missing URLs"
            )
        return image_ids, image_urls

    def _build_points(
        self,
        batch_start: int,
        original_batch,
        pooled_by_rows_batch,
        pooled_by_columns_batch,
        image_ids: List[str],
        image_urls: List[str],
        meta_batch: List[dict],
    ) -> List[models.PointStruct]:
        points: List[models.PointStruct] = []
        use_mean_pooling = bool(config.QDRANT_MEAN_POOLING_ENABLED)

        for offset, (orig, doc_id, image_url, meta) in enumerate(
            zip(original_batch, image_ids, image_urls, meta_batch)
        ):
            rows = None
            cols = None
            if use_mean_pooling and pooled_by_rows_batch and pooled_by_columns_batch:
                rows = pooled_by_rows_batch[offset]
                cols = pooled_by_columns_batch[offset]

            now_iso = datetime.now().isoformat() + "Z"
            payload = {
                "index": batch_start + offset,
                "image_url": image_url,
                "document_id": doc_id,
                "filename": meta.get("filename"),
                "file_size_bytes": meta.get("file_size_bytes"),
                "pdf_page_index": meta.get("pdf_page_index"),
                "total_pages": meta.get("total_pages"),
                "indexed_at": now_iso,
            }

            vectors = {"original": orig}
            if use_mean_pooling and rows is not None and cols is not None:
                vectors["mean_pooling_columns"] = cols
                vectors["mean_pooling_rows"] = rows

            if self.muvera_post and self.muvera_post.enabled:
                try:
                    fde = self.muvera_post.process_document(orig)
                    if fde is not None:
                        vectors["muvera_fde"] = fde
                    else:
                        logger.debug("No MUVERA FDE produced for doc_id=%s", doc_id)
                except Exception as exc:
                    logger.warning(
                        "Failed to compute MUVERA FDE for doc %s: %s", doc_id, exc
                    )

            points.append(
                models.PointStruct(
                    id=doc_id,
                    vector=vectors,
                    payload=payload,
                )
            )

        return points

    def process_single_batch(
        self,
        batch_idx: int,
        batch: List,
        total_images: int,
        progress_cb: Optional[Callable[[int, dict | None], None]] = None,
        skip_progress: bool = False,
    ) -> Tuple[List[models.PointStruct], int]:
        batch_start = batch_idx
        current_batch_size = len(batch)
        image_batch, meta_batch = self._split_batch(batch)

        if skip_progress:
            self._call_progress(progress_cb, batch_start, {"stage": "check_cancel"}, skip_updates=True)
        else:
            self._call_progress(
                progress_cb,
                batch_start,
                {
                    "stage": "embedding",
                    "batch_start": batch_start,
                    "batch_size": current_batch_size,
                    "total": total_images,
                },
            )

        original_batch, pooled_by_rows_batch, pooled_by_columns_batch = self._embed_batch(image_batch)

        if skip_progress:
            self._call_progress(progress_cb, batch_start, {"stage": "check_cancel"}, skip_updates=True)
        else:
            self._call_progress(
                progress_cb,
                batch_start,
                {
                    "stage": "storing",
                    "batch_start": batch_start,
                    "batch_size": current_batch_size,
                    "total": total_images,
                },
            )

        if skip_progress:
            self._call_progress(progress_cb, batch_start, {"stage": "check_cancel"}, skip_updates=True)

        try:
            image_ids, image_urls = self._store_images(batch_start, image_batch)

            points = self._build_points(
                batch_start,
                original_batch,
                pooled_by_rows_batch,
                pooled_by_columns_batch,
                image_ids,
                image_urls,
                meta_batch,
            )
        finally:
            for image in image_batch:
                close = getattr(image, "close", None)
                if callable(close):
                    try:
                        close()
                    except Exception:
                        pass

        return points, batch_start

    def index_documents(
        self,
        images: Iterable,
        total_images: Optional[int] = None,
        progress_cb: Optional[Callable[[int, dict | None], None]] = None,
    ) -> str:
        batch_size = int(config.BATCH_SIZE)

        if isinstance(images, list):
            total = total_images if total_images is not None else len(images)
            image_iter = iter(images)
        else:
            if total_images is None:
                raise ValueError("total_images must be provided when streaming images")
            total = total_images
            image_iter = iter(images)

        if config.ENABLE_PIPELINE_INDEXING and total > batch_size:
            return self._index_documents_pipelined(image_iter, batch_size, total, progress_cb)

        return self._index_documents_sequential(image_iter, batch_size, total, progress_cb)

    def _index_documents_sequential(
        self,
        images_iter: Iterator,
        batch_size: int,
        total_images: int,
        progress_cb: Optional[Callable[[int, dict | None], None]] = None,
    ) -> str:
        completed = 0
        for batch_start, batch in self._batch_iterator(images_iter, batch_size):
            current_batch_size = len(batch)

            points, _ = self.process_single_batch(
                batch_idx=batch_start,
                batch=batch,
                total_images=total_images,
                progress_cb=progress_cb,
            )

            try:
                self.service.upsert(
                    collection_name=self.collection_name,
                    points=points,
                )
            except Exception as exc:
                raise Exception(
                    f"Error during upsert for batch starting at {batch_start}: {exc}"
                ) from exc

            completed += current_batch_size
            progress_value = min(completed, total_images) if total_images > 0 else completed
            self._call_progress(
                progress_cb,
                progress_value,
                {
                    "stage": "upsert",
                    "batch_start": batch_start,
                    "batch_size": current_batch_size,
                    "total": total_images,
                },
            )

        processed = completed if total_images <= 0 else total_images
        return f"Uploaded and converted {processed} pages"

    def _index_documents_pipelined(
        self,
        images_iter: Iterator,
        batch_size: int,
        total_images: int,
        progress_cb: Optional[Callable[[int, dict | None], None]] = None,
    ) -> str:
        max_workers = _estimate_pipeline_workers()
        completed_count = 0
        upsert_futures = []
        batch_iterator = self._batch_iterator(images_iter, batch_size)

        with ThreadPoolExecutor(max_workers=max_workers) as process_executor, ThreadPoolExecutor(max_workers=max_workers) as upsert_executor:
            process_futures = {}

            def submit_next_batch() -> bool:
                try:
                    batch_start, batch = next(batch_iterator)
                except StopIteration:
                    return False
                future = process_executor.submit(
                    self.process_single_batch,
                    batch_idx=batch_start,
                    batch=batch,
                    total_images=total_images,
                    progress_cb=progress_cb,
                    skip_progress=True,
                )
                process_futures[future] = (batch_start, len(batch))
                return True

            for _ in range(max_workers):
                if not submit_next_batch():
                    break

            try:
                while process_futures:
                    done, _ = wait(process_futures.keys(), return_when=FIRST_COMPLETED)
                    for future in done:
                        batch_start, batch_len = process_futures.pop(future)
                        points, idx = future.result()

                        upsert_future = upsert_executor.submit(
                            self.service.upsert,
                            collection_name=self.collection_name,
                            points=points,
                        )
                        upsert_futures.append((upsert_future, batch_start, batch_len, idx))

                        completed_count += batch_len
                        progress_value = min(completed_count, total_images) if total_images > 0 else completed_count
                        self._call_progress(
                            progress_cb,
                            progress_value,
                            {
                                "stage": "processing",
                                "batch_start": idx,
                                "batch_size": batch_len,
                                "total": total_images,
                            },
                        )

                        submit_next_batch()

                for upsert_future, batch_start, batch_len, idx in upsert_futures:
                    try:
                        upsert_future.result()
                    except Exception as exc:  # pragma: no cover - defensive guard
                        raise Exception(
                            f"Upsert failed for batch starting at {batch_start}: {exc}"
                        ) from exc

            except Exception as exc:
                if "cancelled" in str(exc).lower() or exc.__class__.__name__ == "CancellationError":
                    logger.info("Cancelling remaining batches due to cancellation request")
                for future in process_futures:
                    future.cancel()
                for upsert_future, *_ in upsert_futures:
                    upsert_future.cancel()
                raise

        processed = completed_count if total_images <= 0 else total_images
        return f"Uploaded and converted {processed} pages (pipelined mode)"
