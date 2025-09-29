import uuid
import numpy as np
from typing import List, Tuple, Optional, Callable
from PIL import Image
from datetime import datetime
from qdrant_client import QdrantClient, models
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
import queue
import threading

from config import (
    QDRANT_URL,
    QDRANT_COLLECTION_NAME,
    BATCH_SIZE,
    QDRANT_SEARCH_LIMIT,
    QDRANT_PREFETCH_LIMIT,
    QDRANT_ON_DISK,
    QDRANT_ON_DISK_PAYLOAD,
    QDRANT_USE_BINARY,
    QDRANT_BINARY_ALWAYS_RAM,
    QDRANT_SEARCH_IGNORE_QUANT,
    QDRANT_SEARCH_RESCORE,
    QDRANT_SEARCH_OVERSAMPLING,
    ENABLE_PIPELINE_INDEXING,
    MAX_CONCURRENT_BATCHES,
)
from .minio import MinioService
from .colpali import ColPaliClient
from .muvera import MuveraPostprocessor
from api.utils import compute_page_label
import logging

logger = logging.getLogger(__name__)


class QdrantService:
    def __init__(
        self,
        api_client: ColPaliClient = None,
        minio_service: MinioService = None,
        muvera_post: MuveraPostprocessor | None = None,
    ):
        try:
            # Initialize Qdrant client
            self.client = QdrantClient(url=QDRANT_URL)
            self.collection_name = QDRANT_COLLECTION_NAME

            # Use injected dependencies (do not initialize here)
            self.api_client = api_client
            self.minio_service = minio_service
            self.muvera_post = muvera_post
        except Exception as e:
            raise Exception(f"Failed to initialize Qdrant service: {e}")

    def _get_model_dimension(self) -> int:
        """Get the embedding dimension from the API"""
        info = self.api_client.get_info()
        if not info or "dim" not in info:
            raise ValueError(
                "Failed to get model dimension from API. The API might be down or misconfigured."
            )
        return info["dim"]

    def _create_collection_if_not_exists(self):
        """Create Qdrant collection for document storage with proper dimension validation"""
        # Return early if the collection already exists
        try:
            coll = self.client.get_collection(self.collection_name)
            logger.info("Qdrant collection '%s' exists; checking MUVERA vector space", self.collection_name)
            # If MUVERA is enabled, ensure vector exists and has correct size
            if self.muvera_post and self.muvera_post.embedding_size:
                try:
                    vectors = coll.vectors_count or {}
                    # Try to fetch current vector config
                    coll_info = self.client.get_collection(self.collection_name)
                    # If 'muvera_fde' is missing, add it via update
                    if not getattr(coll_info.config.params, "vectors", None) or (
                        isinstance(coll_info.config.params.vectors, dict)
                        and "muvera_fde" not in coll_info.config.params.vectors
                    ):
                        logger.info(
                            "Adding MUVERA vector 'muvera_fde' (dim=%s) to existing collection",
                            int(self.muvera_post.embedding_size),
                        )
                        self.client.update_collection(
                            collection_name=self.collection_name,
                            vectors_config={
                                "muvera_fde": models.VectorParams(
                                    size=int(self.muvera_post.embedding_size),
                                    distance=models.Distance.COSINE,
                                    on_disk=QDRANT_ON_DISK,
                                )
                            },
                        )
                except Exception:
                    # Best-effort; if we can't introspect, proceed
                    logger.warning("Could not verify or add MUVERA vector space; proceeding without update")
                    pass
            return
        except Exception:
            pass

        try:
            # Get the model dimension from API
            model_dim = self._get_model_dimension()

            # Define vector configuration with the correct dimension
            def _vp(include_hnsw: bool = False) -> models.VectorParams:
                quant = (
                    models.BinaryQuantization(
                        binary=models.BinaryQuantizationConfig(
                            always_ram=QDRANT_BINARY_ALWAYS_RAM
                        )
                    )
                    if QDRANT_USE_BINARY
                    else None
                )
                return models.VectorParams(
                    size=model_dim,
                    distance=models.Distance.COSINE,
                    multivector_config=models.MultiVectorConfig(
                        comparator=models.MultiVectorComparator.MAX_SIM
                    ),
                    hnsw_config=(models.HnswConfigDiff(m=0) if include_hnsw else None),
                    on_disk=QDRANT_ON_DISK,
                    quantization_config=quant,
                )

            vector_config = {
                "original": _vp(include_hnsw=True),
                "mean_pooling_columns": _vp(),
                "mean_pooling_rows": _vp(),
            }

            # Add MUVERA single-vector space if enabled
            if self.muvera_post and self.muvera_post.embedding_size:
                vector_config["muvera_fde"] = models.VectorParams(
                    size=int(self.muvera_post.embedding_size),
                    distance=models.Distance.COSINE,
                    on_disk=QDRANT_ON_DISK,
                )

            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=vector_config,
                on_disk_payload=QDRANT_ON_DISK_PAYLOAD,
            )
            logger.info("Created new collection '%s' with model_dim=%s and vectors: %s", self.collection_name, model_dim, list(vector_config.keys()))
        except Exception as e:
            if "already exists" in str(e).lower():
                model_dim = self._get_model_dimension()
                logger.info(
                    "Using existing collection '%s' with model_dim=%s",
                    self.collection_name,
                    model_dim,
                )
            else:
                raise Exception(f"Failed to create collection: {e}")

    def _get_patches(self, image_size: Tuple[int, int]) -> Tuple[int, int]:
        """Get number of patches for image using API"""
        width, height = image_size
        dimensions = [{"width": width, "height": height}]
        results = self.api_client.get_patches(dimensions)
        result = results[0]  # Get first (and only) result
        return result["n_patches_x"], result["n_patches_y"]

    @staticmethod
    def _pool_image_tokens(
        image_embedding_np: np.ndarray,
        start: int,
        patch_len: int,
        x_patches: int,
        y_patches: int,
    ) -> Tuple[List[List[float]], List[List[float]]]:
        """
        Mean-pool image tokens by rows and columns, preserving prefix/postfix tokens.

        Returns:
            pooled_by_rows, pooled_by_columns
        """
        total_tokens = image_embedding_np.shape[0]

        if start < 0 or patch_len <= 0:
            raise ValueError(
                f"Invalid image token boundaries: start={start}, patch_len={patch_len}"
            )

        end = start + patch_len
        if end > total_tokens:
            raise ValueError(
                f"Image token slice out of bounds: end={end}, total_tokens={total_tokens}"
            )

        # Extract sections
        prefix_tokens = image_embedding_np[:start]
        image_patch_tokens = image_embedding_np[start:end]
        postfix_tokens = image_embedding_np[end:]

        # Reshape to [x_patches, y_patches, dim]
        if patch_len != x_patches * y_patches:
            raise ValueError(
                f"image_patch_len ({patch_len}) != x_patches*y_patches ({x_patches * y_patches})"
            )

        dim = image_patch_tokens.shape[-1]
        image_tokens = image_patch_tokens.reshape(x_patches, y_patches, dim)

        # Mean pooling across rows/columns
        pooled_by_rows = np.mean(image_tokens, axis=0)  # [y_patches, dim]
        pooled_by_columns = np.mean(image_tokens, axis=1)  # [x_patches, dim]

        # Add back prefix/postfix
        pooled_by_rows = np.concatenate(
            [prefix_tokens, pooled_by_rows.reshape(-1, dim), postfix_tokens], axis=0
        ).tolist()
        pooled_by_columns = np.concatenate(
            [prefix_tokens, pooled_by_columns.reshape(-1, dim), postfix_tokens], axis=0
        ).tolist()

        return pooled_by_rows, pooled_by_columns

    def _embed_and_mean_pool_batch(self, image_batch: List[Image.Image]):
        """
        Embed images via API and create mean pooled representations using explicit
        image-token boundaries provided by the API (no midpoint guessing).
        """
        # API returns per-image dicts: {embedding, image_patch_start, image_patch_len}
        api_items = self.api_client.embed_images(image_batch)

        # Batch get patches for all images
        dimensions = [
            {"width": image.size[0], "height": image.size[1]} for image in image_batch
        ]
        patch_results = self.api_client.get_patches(dimensions)

        pooled_by_rows_batch = []
        pooled_by_columns_batch = []
        original_batch = []

        for item, image, patch_result in zip(api_items, image_batch, patch_results):
            if isinstance(item, dict):
                embedding_list = item.get("embedding")
                start = item.get("image_patch_start", -1)
                patch_len = item.get("image_patch_len", 0)
            else:
                raise Exception(
                    "embed_images() returned embeddings without image-token boundaries"
                )

            image_embedding_np = np.asarray(embedding_list, dtype=np.float32)
            x_patches = patch_result["n_patches_x"]
            y_patches = patch_result["n_patches_y"]

            # Pool using explicit boundaries; sanity checks inside
            pooled_by_rows, pooled_by_columns = self._pool_image_tokens(
                image_embedding_np=image_embedding_np,
                start=int(start),
                patch_len=int(patch_len),
                x_patches=int(x_patches),
                y_patches=int(y_patches),
            )

            original_batch.append(image_embedding_np.tolist())
            pooled_by_rows_batch.append(pooled_by_rows)
            pooled_by_columns_batch.append(pooled_by_columns)

        return original_batch, pooled_by_rows_batch, pooled_by_columns_batch

    def _process_single_batch(
        self,
        batch_idx: int,
        batch: List,
        total_images: int,
        progress_cb: Optional[Callable[[int, dict | None], None]] = None,
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
        if progress_cb is not None:
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

        # STEP 1: Embed images (SLOW on CPU)
        try:
            original_batch, pooled_by_rows_batch, pooled_by_columns_batch = (
                self._embed_and_mean_pool_batch(image_batch)
            )
        except Exception as e:
            raise Exception(f"Error during embed: {e}")

        # Notify storage phase
        if progress_cb is not None:
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
        self._create_collection_if_not_exists()

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
                points, batch_idx = self._process_single_batch(
                    batch_idx=i,
                    batch=batch,
                    total_images=total_images,
                    progress_cb=progress_cb,
                )

                # Upsert to Qdrant
                try:
                    self.client.upsert(
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
        
        This overlaps embedding (slow) with uploading and upserting (I/O-bound).
        """
        max_workers = MAX_CONCURRENT_BATCHES if MAX_CONCURRENT_BATCHES > 0 else 2
        completed_count = 0
        
        with tqdm(total=total_images, desc="Indexing progress (pipelined)") as pbar:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all batch processing jobs
                futures = {}
                for i in range(0, len(images), batch_size):
                    batch = images[i : i + batch_size]
                    future = executor.submit(
                        self._process_single_batch,
                        batch_idx=i,
                        batch=batch,
                        total_images=total_images,
                        progress_cb=progress_cb,
                    )
                    futures[future] = (i, len(batch))
                
                # Process completed batches and upsert in order of completion
                try:
                    for future in as_completed(futures):
                        batch_idx, batch_size_processed = futures[future]
                        try:
                            points, idx = future.result()
                            
                            # Upsert to Qdrant (happens concurrently with other embedding jobs)
                            self.client.upsert(
                                collection_name=self.collection_name,
                                points=points,
                            )
                            
                            completed_count += batch_size_processed
                            pbar.update(batch_size_processed)
                            
                            # Notify progress
                            if progress_cb is not None:
                                try:
                                    progress_cb(completed_count, {
                                        "stage": "upsert",
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
                except Exception as cancel_err:
                    # Check if it's a cancellation exception
                    if "cancelled" in str(cancel_err).lower() or cancel_err.__class__.__name__ == "CancellationError":
                        # Cancel all remaining futures
                        logger.info("Cancelling remaining batches...")
                        for future in futures:
                            future.cancel()
                        raise
        return f"Uploaded and converted {len(images)} pages (pipelined mode)"

    def _batch_embed_query(self, query_batch: List[str]) -> np.ndarray:
        """Embed query batch using API (returns the first, since we submit one)."""
        query_embeddings = self.api_client.embed_queries(
            query_batch
        )  # List[List[List[float]]]
        return np.array(query_embeddings[0]) if query_embeddings else np.array([])

    def _reranking_search_batch(
        self,
        query_embeddings_batch: List[np.ndarray],
        search_limit: int = QDRANT_SEARCH_LIMIT,
        prefetch_limit: int = QDRANT_PREFETCH_LIMIT,
        qdrant_filter: Optional[models.Filter] = None,
    ):
        """Perform two-stage retrieval with MUVERA-first (if enabled) and multivector rerank."""
        # Optional quantization-aware search params
        params = None
        if QDRANT_USE_BINARY:
            params = models.SearchParams(
                quantization=models.QuantizationSearchParams(
                    ignore=QDRANT_SEARCH_IGNORE_QUANT,
                    rescore=QDRANT_SEARCH_RESCORE,
                    oversampling=QDRANT_SEARCH_OVERSAMPLING,
                )
            )
        search_queries = []
        for query_embedding in query_embeddings_batch:
            # If MUVERA available, compute query FDE
            muvera_query = None
            if self.muvera_post and self.muvera_post.enabled:
                try:
                    muvera_query = self.muvera_post.process_query(query_embedding.tolist())
                    logger.debug("MUVERA query FDE generated: len=%s", len(muvera_query) if muvera_query else None)
                except Exception as e:
                    logger.warning("MUVERA query FDE failed, falling back: %s", e)
                    muvera_query = None

            if muvera_query is not None:
                # First-stage using MUVERA single-vector, prefetch multivectors for rerank
                logger.info("Search using MUVERA first-stage with prefetch for rerank")
                req = models.QueryRequest(
                    query=muvera_query,
                    prefetch=[
                        models.Prefetch(
                            query=query_embedding.tolist(),
                            limit=prefetch_limit,
                            using="mean_pooling_columns",
                        ),
                        models.Prefetch(
                            query=query_embedding.tolist(),
                            limit=prefetch_limit,
                            using="mean_pooling_rows",
                        ),
                    ],
                    limit=search_limit,
                    with_payload=True,
                    with_vector=False,
                    using="muvera_fde",
                    filter=qdrant_filter,
                    params=params,
                )
            else:
                # Fallback: original multivector pipeline
                logger.info("Search using multivector-only pipeline (MUVERA unavailable)")
                req = models.QueryRequest(
                    query=query_embedding.tolist(),
                    prefetch=[
                        models.Prefetch(
                            query=query_embedding.tolist(),
                            limit=prefetch_limit,
                            using="mean_pooling_columns",
                        ),
                        models.Prefetch(
                            query=query_embedding.tolist(),
                            limit=prefetch_limit,
                            using="mean_pooling_rows",
                        ),
                    ],
                    limit=search_limit,
                    with_payload=True,
                    with_vector=False,
                    using="original",
                    filter=qdrant_filter,
                    params=params,
                )
            search_queries.append(req)
        return self.client.query_batch_points(
            collection_name=self.collection_name, requests=search_queries
        )

    def search_with_metadata(
        self, query: str, k: int = 5, payload_filter: Optional[dict] = None
    ):
        """Search and return images alongside full Qdrant payload metadata.

        payload_filter: optional dict of equality filters, e.g.
          {"filename": "doc.pdf", "pdf_page_index": 3}
        """
        query_embedding = self._batch_embed_query([query])
        q_filter = None
        if payload_filter:
            try:
                conditions = []
                for kf, vf in payload_filter.items():
                    conditions.append(
                        models.FieldCondition(
                            key=str(kf), match=models.MatchValue(value=vf)
                        )
                    )
                q_filter = models.Filter(must=conditions) if conditions else None
            except Exception:
                q_filter = None
        # Ensure we request at least k results from Qdrant; otherwise k>QDRANT_SEARCH_LIMIT
        # would be silently capped by the default.
        effective_limit = max(int(k), 1)
        search_results = self._reranking_search_batch(
            [query_embedding], search_limit=effective_limit, qdrant_filter=q_filter
        )

        items = []
        if search_results and search_results[0].points:
            for i, point in enumerate(search_results[0].points[:k]):
                try:
                    image_url = (
                        point.payload.get("image_url") if point.payload else None
                    )
                    if image_url and self.minio_service:
                        image = self.minio_service.get_image(image_url)
                        items.append(
                            {
                                "image": image,
                                "payload": point.payload,
                                "label": compute_page_label(point.payload),
                                "score": getattr(point, "score", None),
                            }
                        )
                    else:
                        raise Exception(
                            f"Cannot retrieve image for point {i}. "
                            f"Image URL: {image_url}, MinIO available: {self.minio_service is not None}"
                        )
                except Exception as e:
                    raise Exception(
                        f"Error retrieving image from MinIO for point {i}: {e}"
                    )
        return items

    def search(self, query: str, k: int = 5):
        """Search for relevant documents using Qdrant and retrieve images from MinIO.

        Returns a list suitable for Gradio Gallery: (image, caption), while
        internally enabling richer metadata retrieval via `search_with_metadata`.
        """
        items = self.search_with_metadata(query, k)
        results = []
        for item in items:
            results.append((item.get("image"), item["label"]))
        return results

    # -----------------------
    # Maintenance helpers
    # -----------------------
    def clear_collection(self) -> str:
        """Delete and recreate the configured collection to remove all points."""
        try:
            self.client.delete_collection(collection_name=self.collection_name)
        except Exception as e:
            # If not exists, ignore and proceed to (re)create
            if "not found" not in str(e).lower():
                raise Exception(f"Failed to delete collection: {e}")

        # Recreate with correct vectors config
        self._create_collection_if_not_exists()
        return f"Cleared Qdrant collection '{self.collection_name}'."

    def health_check(self) -> bool:
        """Check if Qdrant service is healthy and accessible."""
        try:
            _ = self.client.get_collection(self.collection_name)
            return True
        except Exception as e:
            logger.error(f"Qdrant health check failed: {e}")
            return False
