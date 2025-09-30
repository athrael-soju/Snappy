"""Document indexing operations for Qdrant."""

import uuid
import logging
from typing import List, Tuple, Optional, Callable
from PIL import Image
from datetime import datetime
from qdrant_client import models
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

from config import (
    BATCH_SIZE,
    ENABLE_PIPELINE_INDEXING,
    MAX_CONCURRENT_BATCHES,
    MINIO_IMAGE_QUALITY,
)

logger = logging.getLogger(__name__)


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
        """Initialize document indexer.
        
        Args:
            qdrant_client: Qdrant client instance
            collection_name: Name of the collection
            embedding_processor: EmbeddingProcessor instance
            minio_service: MinIO service for image storage
            muvera_post: Optional MUVERA postprocessor
        """
        self.service = qdrant_client
        self.collection_name = collection_name
        self.embedding_processor = embedding_processor
        self.minio_service = minio_service
        self.muvera_post = muvera_post

    def process_single_batch(
        self,
        batch_idx: int,
        batch: List,
        total_images: int,
        progress_cb: Optional[Callable[[int, dict | None], None]] = None,
        skip_progress: bool = False,  # Skip progress reporting for pipelined mode
    ) -> Tuple[List[models.PointStruct], int]:
        """Process a single batch: embed, store, and prepare points.
        
        Returns:
            Tuple of (points, batch_start_index)
        """
        current_batch_size = len(batch)
        i = batch_idx
        
        # Split into image and metadata batches, preserving order
        image_batch: List[Image.Image] = [
            (b if isinstance(b, Image.Image) else b.get("image")) for b in batch
        ]
        meta_batch: List[dict] = [
            (
                {
                    k: v
                    for k, v in (
                        {} if isinstance(b, Image.Image) else dict(b)
                    ).items()
                    if k != "image"
                }
            )
            for b in batch
        ]

        # Notify that embedding is starting (this is the slow step on CPU)
        # Skip progress updates during concurrent batch processing to avoid out-of-order updates
        if progress_cb is not None and not skip_progress:
            try:
                progress_cb(i, {
                    "stage": "embedding",
                    "batch_start": i,
                    "batch_size": current_batch_size,
                    "total": total_images,
                })
            except Exception as ex:
                # Check if it's a cancellation exception (from progress callback)
                if "cancelled" in str(ex).lower() or ex.__class__.__name__ == "CancellationError":
                    # Re-raise cancellation to stop processing
                    raise
                # Swallow other progress callback errors
                pass
        
        # Check for cancellation even when skipping progress
        if progress_cb is not None and skip_progress:
            try:
                progress_cb(i, {"stage": "check_cancel"})
            except Exception as ex:
                if "cancelled" in str(ex).lower() or ex.__class__.__name__ == "CancellationError":
                    raise

        # STEP 1: Embed images (SLOW on CPU)
        try:
            original_batch, pooled_by_rows_batch, pooled_by_columns_batch = (
                self.embedding_processor.embed_and_mean_pool_batch(image_batch)
            )
        except Exception as e:
            raise Exception(f"Error during embed: {e}")

        # Notify storage phase
        if progress_cb is not None and not skip_progress:
            try:
                progress_cb(i, {
                    "stage": "storing",
                    "batch_start": i,
                    "batch_size": current_batch_size,
                    "total": total_images,
                })
            except Exception as ex:
                # Check if it's a cancellation exception (from progress callback)
                if "cancelled" in str(ex).lower() or ex.__class__.__name__ == "CancellationError":
                    # Re-raise cancellation to stop processing
                    raise
                # Swallow other progress callback errors
                pass
        
        # Check for cancellation even when skipping progress
        if progress_cb is not None and skip_progress:
            try:
                progress_cb(i, {"stage": "check_cancel"})
            except Exception as ex:
                if "cancelled" in str(ex).lower() or ex.__class__.__name__ == "CancellationError":
                    raise

        # STEP 2: Store images in MinIO (I/O-bound, parallelized internally)
        image_urls = []
        if self.minio_service:
            try:
                # Generate deterministic image IDs aligned with the batch
                image_ids = [
                    str(uuid.uuid4()) for _ in range(current_batch_size)
                ]
                image_url_dict = self.minio_service.store_images_batch(
                    image_batch,
                    image_ids=image_ids,
                    quality=MINIO_IMAGE_QUALITY,  # JPEG quality for compression
                )
                # Keep alignment by resolving URL per ID
                image_urls = [
                    image_url_dict.get(img_id) for img_id in image_ids
                ]
            except Exception as e:
                raise Exception(
                    f"Error storing images in MinIO for batch starting at {i}: {e}"
                )
        else:
            raise Exception("MinIO service not available")

        # STEP 3: Build points for Qdrant
        points = []
        for j in range(current_batch_size):
            orig = original_batch[j]
            rows = pooled_by_rows_batch[j]
            cols = pooled_by_columns_batch[j]
            image_url = image_urls[j]
            meta = meta_batch[j] if j < len(meta_batch) else {}

            # Skip if image failed to upload
            if not image_url:
                raise Exception(
                    f"Image failed to upload for batch starting at {i}: {image_url}"
                )

            doc_id = image_ids[j]

            # Prepare payload with MinIO URL
            now_iso = datetime.now().isoformat() + "Z"
            payload = {
                "index": i + j,
                "image_url": image_url,
                "document_id": doc_id,
                "filename": meta.get("filename"),
                "file_size_bytes": meta.get("file_size_bytes"),
                "pdf_page_index": meta.get("pdf_page_index"),
                "total_pages": meta.get("total_pages"),
                "indexed_at": now_iso,
            }

            vectors = {
                "mean_pooling_columns": cols,
                "original": orig,
                "mean_pooling_rows": rows,
            }

            # Compute and attach MUVERA FDE if available
            if self.muvera_post and self.muvera_post.enabled:
                try:
                    fde = self.muvera_post.process_document(orig)
                    if fde is not None:
                        vectors["muvera_fde"] = fde
                    else:
                        logger.debug("No MUVERA FDE produced for doc_id=%s", doc_id)
                except Exception as e:
                    logger.warning(
                        "Failed to compute MUVERA FDE for doc %s: %s", doc_id, e
                    )

            points.append(
                models.PointStruct(
                    id=doc_id,
                    vector=vectors,
                    payload=payload,
                )
            )

        return points, i

    def index_documents(self, images: List[Image.Image], progress_cb: Optional[Callable[[int, dict | None], None]] = None):
        """Index documents in Qdrant with rich payload metadata.

        Accepts either a list of PIL Images or a list of dicts, where each dict
        contains at least the key 'image': PIL.Image plus optional metadata
        keys, e.g. 'filename', 'file_size_bytes', 'pdf_page_index',
        'total_pages', 'page_width_px', 'page_height_px'.
        
        Uses pipelined processing if ENABLE_PIPELINE_INDEXING=True to overlap
        embedding, storage, and upserting operations.
        """
        batch_size = int(BATCH_SIZE)
        total_images = len(images)
        
        # Choose processing mode based on configuration
        if ENABLE_PIPELINE_INDEXING and total_images > batch_size:
            return self._index_documents_pipelined(images, batch_size, total_images, progress_cb)
        else:
            return self._index_documents_sequential(images, batch_size, total_images, progress_cb)

    def _index_documents_sequential(
        self, 
        images: List, 
        batch_size: int, 
        total_images: int, 
        progress_cb: Optional[Callable[[int, dict | None], None]] = None
    ) -> str:
        """Sequential processing: process one batch fully before starting the next."""
        with tqdm(total=total_images, desc="Indexing progress") as pbar:
            for i in range(0, len(images), batch_size):
                batch = images[i : i + batch_size]
                current_batch_size = len(batch)

                # Process batch: embed, store, build points
                points, batch_idx = self.process_single_batch(
                    batch_idx=i,
                    batch=batch,
                    total_images=total_images,
                    progress_cb=progress_cb,
                )

                # Upsert to Qdrant
                try:
                    self.service.upsert(
                        collection_name=self.collection_name,
                        points=points,
                    )
                except Exception as e:
                    raise Exception(
                        f"Error during upsert for batch starting at {i}: {e}"
                    )

                pbar.update(current_batch_size)
                # Notify progress callback
                if progress_cb is not None:
                    try:
                        progress_cb(min(i + current_batch_size, total_images), {
                            "stage": "upsert",
                            "batch_start": i,
                            "batch_size": current_batch_size,
                            "total": total_images,
                        })
                    except Exception:
                        pass

        return f"Uploaded and converted {len(images)} pages"

    def _index_documents_pipelined(
        self, 
        images: List, 
        batch_size: int, 
        total_images: int, 
        progress_cb: Optional[Callable[[int, dict | None], None]] = None
    ) -> str:
        """Pipelined processing: process multiple batches concurrently with controlled parallelism.
        
        This overlaps embedding (slow), MinIO uploads (I/O-bound), and Qdrant upserts (I/O-bound)
        for maximum throughput. Uses separate thread pools for processing and upserting.
        """
        max_workers = MAX_CONCURRENT_BATCHES if MAX_CONCURRENT_BATCHES > 0 else 2
        completed_count = 0
        upsert_futures = []
        
        with tqdm(total=total_images, desc="Indexing progress (pipelined)") as pbar:
            # Separate executor for upserts to avoid blocking the processing pipeline
            with ThreadPoolExecutor(max_workers=max_workers) as process_executor, \
                 ThreadPoolExecutor(max_workers=max_workers) as upsert_executor:
                
                # Submit all batch processing jobs
                process_futures = {}
                for i in range(0, len(images), batch_size):
                    batch = images[i : i + batch_size]
                    future = process_executor.submit(
                        self.process_single_batch,
                        batch_idx=i,
                        batch=batch,
                        total_images=total_images,
                        progress_cb=progress_cb,
                        skip_progress=True,  # Skip progress updates from worker threads
                    )
                    process_futures[future] = (i, len(batch))
                
                # Process completed batches and submit upserts concurrently
                try:
                    for future in as_completed(process_futures):
                        batch_idx, batch_size_processed = process_futures[future]
                        try:
                            points, idx = future.result()
                            
                            # Submit upsert to separate executor (non-blocking)
                            # This allows embedding to continue while upserts happen in parallel
                            upsert_future = upsert_executor.submit(
                                self.service.upsert,
                                collection_name=self.collection_name,
                                points=points,
                            )
                            upsert_futures.append((upsert_future, batch_idx, batch_size_processed, idx))
                            
                            completed_count += batch_size_processed
                            pbar.update(batch_size_processed)
                            
                            # Notify progress - report cumulative completed count
                            if progress_cb is not None:
                                try:
                                    progress_cb(completed_count, {
                                        "stage": "processing",  # Generic stage for pipelined mode
                                        "batch_start": idx,
                                        "batch_size": batch_size_processed,
                                        "total": total_images,
                                    })
                                except Exception as ex:
                                    # Check if it's a cancellation exception
                                    if "cancelled" in str(ex).lower() or ex.__class__.__name__ == "CancellationError":
                                        # Cancellation detected, stop processing
                                        raise
                                    # Swallow other progress callback errors
                                    pass
                                    
                        except Exception as batch_err:
                            # Check if it's a cancellation exception
                            if "cancelled" in str(batch_err).lower() or batch_err.__class__.__name__ == "CancellationError":
                                logger.info(f"Batch {batch_idx} cancelled")
                                raise
                            # Other errors
                            logger.error(f"Batch {batch_idx} failed: {batch_err}")
                            raise Exception(f"Error processing batch starting at {batch_idx}: {batch_err}")
                    
                    # Wait for all upserts to complete and check for errors
                    for upsert_fut, b_idx, b_size, idx in upsert_futures:
                        try:
                            upsert_fut.result()  # Will raise if upsert failed
                        except Exception as upsert_err:
                            logger.error(f"Upsert failed for batch {b_idx}: {upsert_err}")
                            raise Exception(f"Upsert failed for batch starting at {b_idx}: {upsert_err}")
                            
                except Exception as cancel_err:
                    # Check if it's a cancellation exception
                    if "cancelled" in str(cancel_err).lower() or cancel_err.__class__.__name__ == "CancellationError":
                        # Cancel all remaining futures
                        logger.info("Cancelling remaining batches...")
                        for future in process_futures:
                            future.cancel()
                        for upsert_fut, _, _, _ in upsert_futures:
                            upsert_fut.cancel()
                        raise
        return f"Uploaded and converted {len(images)} pages (pipelined mode)"
