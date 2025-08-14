import uuid
import warnings
import numpy as np
from typing import List, Tuple, Optional
from PIL import Image
from datetime import datetime
from qdrant_client import QdrantClient, models
from tqdm import tqdm

from config import (
    QDRANT_URL,
    QDRANT_COLLECTION_NAME,
    BATCH_SIZE,
    QDRANT_SEARCH_LIMIT,
    QDRANT_PREFETCH_LIMIT,
)
from .minio import MinioService
from .colpali import ColPaliClient


class QdrantService:
    def __init__(self, api_client: ColPaliClient = None):
        try:
            # Initialize Qdrant client
            self.client = QdrantClient(url=QDRANT_URL)
            self.collection_name = QDRANT_COLLECTION_NAME

            # Use API client for embeddings
            self.api_client = api_client or ColPaliClient()

            # Check API health on initialization
            if not self.api_client.health_check():
                raise Exception(
                    "ColPali API health check failed. Please ensure the API server is running."
                )

            # Initialize MinIO service for image storage
            self.minio_service = MinioService()
            if not self.minio_service.health_check():
                raise Exception(
                    "MinIO service health check failed. Please ensure MinIO server is running."
                )
        except Exception as e:
            raise Exception(f"Failed to initialize Qdrant service: {e}")

        # Create collection if it doesn't exist
        self._create_collection_if_not_exists()

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
        try:
            # Get the model dimension from API
            model_dim = self._get_model_dimension()

            # Define vector configuration with the correct dimension
            vector_config = {
                "original": models.VectorParams(
                    size=model_dim,
                    distance=models.Distance.COSINE,
                    multivector_config=models.MultiVectorConfig(
                        comparator=models.MultiVectorComparator.MAX_SIM
                    ),
                    hnsw_config=models.HnswConfigDiff(m=0),
                ),
                "mean_pooling_columns": models.VectorParams(
                    size=model_dim,
                    distance=models.Distance.COSINE,
                    multivector_config=models.MultiVectorConfig(
                        comparator=models.MultiVectorComparator.MAX_SIM
                    ),
                ),
                "mean_pooling_rows": models.VectorParams(
                    size=model_dim,
                    distance=models.Distance.COSINE,
                    multivector_config=models.MultiVectorConfig(
                        comparator=models.MultiVectorComparator.MAX_SIM
                    ),
                ),
            }

            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=vector_config,
            )
            print(f"Created new collection with dimension: {model_dim}")
        except Exception as e:
            if "already exists" in str(e):
                model_dim = self._get_model_dimension()
                print(
                    f"Using existing collection: {self.collection_name} with dimension: {model_dim}"
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
                f"image_patch_len ({patch_len}) != x_patches*y_patches ({x_patches*y_patches})"
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

    def index_documents(self, images: List[Image.Image]):
        """Index documents in Qdrant with rich payload metadata.

        Accepts either a list of PIL Images or a list of dicts, where each dict
        contains at least the key 'image': PIL.Image plus optional metadata
        keys, e.g. 'filename', 'file_size_bytes', 'pdf_page_index',
        'total_pages', 'page_width_px', 'page_height_px'.
        """
        batch_size = int(BATCH_SIZE)

        with tqdm(total=len(images), desc="Uploading progress") as pbar:
            for i in range(0, len(images), batch_size):
                batch = images[i : i + batch_size]
                current_batch_size = len(batch)

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

                try:
                    original_batch, pooled_by_rows_batch, pooled_by_columns_batch = (
                        self._embed_and_mean_pool_batch(image_batch)
                    )
                except Exception as e:
                    raise Exception(f"Error during embed: {e}")

                # Store images in MinIO (if available) and upload each document individually
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

                for j in range(current_batch_size):
                    try:
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

                        # Create document ID (use the same as image id for 1:1 mapping)
                        doc_id = image_url.rsplit("/", 1)[-1].split(".", 1)[0]

                        # Prepare payload with MinIO URL
                        now_iso = datetime.now().isoformat() + "Z"

                        # Minimal payload: drop UI-specific label/size fields; compute labels at query time
                        payload = {
                            "index": i + j,  # global index in this session
                            "image_url": image_url,
                            "document_id": doc_id,
                            # Core metadata used to compute labels client-side
                            "filename": meta.get("filename"),
                            "file_size_bytes": meta.get("file_size_bytes"),
                            "pdf_page_index": meta.get("pdf_page_index"),
                            "total_pages": meta.get("total_pages"),
                            "indexed_at": now_iso,
                        }

                        self.client.upload_collection(
                            collection_name=self.collection_name,
                            vectors={
                                "mean_pooling_columns": np.asarray(
                                    [cols], dtype=np.float32
                                ),
                                "original": np.asarray([orig], dtype=np.float32),
                                "mean_pooling_rows": np.asarray(
                                    [rows], dtype=np.float32
                                ),
                            },
                            payload=[payload],
                            ids=[doc_id],
                        )
                    except Exception as e:
                        raise Exception(f"Error during upsert for image {i + j}: {e}")

                pbar.update(current_batch_size)

        return f"Uploaded and converted {len(images)} pages"

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
        """Perform two-stage retrieval with multivectors"""
        search_queries = [
            models.QueryRequest(
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
            )
            for query_embedding in query_embeddings_batch
        ]
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
        search_results = self._reranking_search_batch(
            [query_embedding], qdrant_filter=q_filter
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
                                "payload": point.payload or {},
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
            payload = item.get("payload", {})
            # Compute label from available metadata (filename + pdf_page_index/total_pages)
            try:
                fname = payload.get("filename")
                page_num = payload.get("pdf_page_index")
                total = payload.get("total_pages")
                if fname and page_num and total:
                    page_info = f"{fname} — {page_num}/{total}"
                elif fname and page_num:
                    page_info = f"{fname} — {page_num}"
                elif page_num and total:
                    page_info = f"Page {page_num}/{total}"
                elif page_num:
                    page_info = f"Page {page_num}"
                else:
                    page_info = fname or f"Index {payload.get('index', '')}"
            except Exception:
                page_info = f"Index {payload.get('index', '')}"
            results.append((item.get("image"), page_info))
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

    def clear_all(self) -> str:
        """Clear Qdrant collection and all MinIO images. Returns a summary string."""
        q_msg = self.clear_collection()
        try:
            res = self.minio_service.clear_images()
            m_msg = f"Cleared MinIO images: deleted={res.get('deleted')}, failed={res.get('failed')}"
        except Exception as e:
            m_msg = f"MinIO clear failed: {e}"
        return f"{q_msg} {m_msg}"
