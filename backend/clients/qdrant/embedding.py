"""Embedding and pooling operations for image processing."""

import logging
from concurrent.futures import ThreadPoolExecutor
from typing import TYPE_CHECKING, Any, List, Optional, Tuple

import numpy as np
from PIL import Image

if TYPE_CHECKING:
    from clients.colpali import ColPaliClient

    from backend import config as config  # type: ignore
else:  # pragma: no cover - runtime import for application execution
    import config  # type: ignore

logger = logging.getLogger(__name__)


class EmbeddingProcessor:
    """Handles embedding and pooling operations for images."""

    def __init__(self, api_client: Optional["ColPaliClient"] = None) -> None:
        """Initialize embedding processor.

        Args:
            api_client: ColPali client for embedding operations
        """
        self.api_client = api_client

    def _require_client(self) -> "ColPaliClient":
        if self.api_client is None:
            raise ValueError("ColPali API client is not initialized")
        return self.api_client

    def get_patches(self, image_size: Tuple[int, int]) -> Tuple[int, int]:
        """Get number of patches for image using API."""
        api_client = self._require_client()
        width, height = image_size
        dimensions = [{"width": width, "height": height}]
        results = api_client.get_patches(dimensions)
        result = results[0]  # Get first (and only) result
        return int(result["n_patches_x"]), int(result["n_patches_y"])

    @staticmethod
    def pool_image_tokens(
        image_embedding_np: np.ndarray,
        start: int,
        patch_len: int,
        x_patches: int,
        y_patches: int,
        patch_indices: Optional[List[int]] = None,
    ) -> Tuple[List[List[float]], List[List[float]]]:
        """Mean-pool image tokens by rows and columns, preserving prefix/postfix tokens."""
        total_tokens = image_embedding_np.shape[0]

        if patch_len <= 0:
            raise ValueError(
                f"Invalid image token boundaries: start={start}, patch_len={patch_len}"
            )

        indices: Optional[np.ndarray]
        if patch_indices:
            indices_array = np.array(sorted(set(int(idx) for idx in patch_indices)))
            if indices_array.size != patch_len:
                raise ValueError(
                    "image_patch_len does not match the number of image_patch_indices"
                )
            indices = indices_array
        else:
            if start < 0:
                raise ValueError("image_patch_start was not provided")
            end = start + patch_len
            if end > total_tokens:
                raise ValueError(
                    f"Image token slice out of bounds: end={end}, total_tokens={total_tokens}"
                )
            indices = None

        if indices is None:
            # Contiguous legacy path
            prefix_tokens = image_embedding_np[:start]
            image_patch_tokens = image_embedding_np[start : start + patch_len]
            postfix_tokens = image_embedding_np[start + patch_len :]
        else:
            image_patch_tokens = image_embedding_np[indices]
            prefix_tokens = np.array([])
            postfix_tokens = np.array([])

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

        pooled_rows_replacement = pooled_by_rows.reshape(-1, dim)
        pooled_cols_replacement = pooled_by_columns.reshape(-1, dim)

        if indices is None:
            # Add back prefix/postfix using contiguous slice boundaries
            postfix_tokens = image_embedding_np[start + patch_len :]
            pooled_by_rows = np.concatenate(
                [prefix_tokens, pooled_rows_replacement, postfix_tokens], axis=0
            ).tolist()
            pooled_by_columns = np.concatenate(
                [prefix_tokens, pooled_cols_replacement, postfix_tokens], axis=0
            ).tolist()
        else:
            indices_set = set(indices.tolist())

            def replace_tokens(
                replacement: np.ndarray,
            ) -> List[List[float]]:
                emitted_replacement = False
                output: List[np.ndarray] = []
                for idx in range(total_tokens):
                    if idx in indices_set:
                        if not emitted_replacement:
                            for token in replacement:
                                output.append(token)
                            emitted_replacement = True
                        continue
                    output.append(image_embedding_np[idx])
                return [token.tolist() for token in output]

            pooled_by_rows = replace_tokens(pooled_rows_replacement)
            pooled_by_columns = replace_tokens(pooled_cols_replacement)

        return pooled_by_rows, pooled_by_columns

    def pool_single_image(self, item, image, patch_result):
        """Pool a single image's embeddings (for parallel execution)."""
        if isinstance(item, dict):
            embedding_list = item.get("embedding")
            start = item.get("image_patch_start", -1)
            patch_len = item.get("image_patch_len", 0)
            raw_indices = item.get("image_patch_indices")
            patch_indices = (
                [int(idx) for idx in raw_indices]
                if isinstance(raw_indices, list)
                else None
            )
        else:
            raise ValueError(
                "embed_images() returned embeddings without image-token boundaries"
            )

        if embedding_list is None:
            raise ValueError("Embedding list missing from API response")

        image_embedding_np = np.asarray(embedding_list, dtype=np.float32)
        x_patches = patch_result["n_patches_x"]
        y_patches = patch_result["n_patches_y"]

        # Pool using explicit boundaries; sanity checks inside
        pooled_by_rows, pooled_by_columns = self.pool_image_tokens(
            image_embedding_np=image_embedding_np,
            start=int(start),
            patch_len=int(patch_len),
            x_patches=int(x_patches),
            y_patches=int(y_patches),
            patch_indices=patch_indices,
        )

        return image_embedding_np.tolist(), pooled_by_rows, pooled_by_columns

    def embed_and_mean_pool_batch(self, image_batch: List[Image.Image]):
        """Embed images via API and optionally perform mean pooling."""
        api_client = self._require_client()
        # API returns per-image dicts: {embedding, image_patch_start, image_patch_len, image_patch_indices}
        api_items_raw = api_client.embed_images(image_batch)
        api_items: List[dict[str, Any]] = []
        for raw_item in api_items_raw:
            if not isinstance(raw_item, dict):
                raise ValueError("embed_images() returned non-dict response")
            api_items.append(raw_item)

        # Extract original embeddings
        original_batch = []
        for item in api_items:
            if isinstance(item, dict) and "embedding" in item:
                original_batch.append(item["embedding"])
            else:
                raise ValueError(
                    "embed_images() returned data without embedding entries"
                )

        # Skip pooling entirely if disabled
        if not bool(config.QDRANT_MEAN_POOLING_ENABLED):
            return original_batch, [], []

        dimensions = [
            {"width": image.width, "height": image.height} for image in image_batch
        ]
        patch_results_raw = api_client.get_patches(dimensions)
        patch_results: List[dict[str, Any]] = []
        for patch in patch_results_raw:
            if not isinstance(patch, dict):
                raise ValueError("get_patches() returned non-dict response")
            patch_results.append(patch)

        for idx, patch in enumerate(patch_results):
            patch_error = patch.get("error")
            if patch_error:
                raise RuntimeError(
                    "QDRANT_MEAN_POOLING_ENABLED=True but the ColPali /patches"
                    f" endpoint reported an error for image {idx}: {patch_error}. "
                    "Disable mean pooling or switch to a model that exposes patch counts."
                )

            if "n_patches_x" not in patch or "n_patches_y" not in patch:
                raise RuntimeError(
                    "QDRANT_MEAN_POOLING_ENABLED=True but the ColPali service did not"
                    f" return 'n_patches_x'/'n_patches_y' for image {idx}. "
                    "This model may not support patch estimation; disable mean pooling."
                )

        pooled_by_rows_batch = []
        pooled_by_columns_batch = []

        # For batches larger than 2, use parallel pooling
        if len(api_items) > 2:
            with ThreadPoolExecutor(max_workers=min(8, len(api_items))) as executor:
                results = list(
                    executor.map(
                        lambda args: self.pool_single_image(args[0], args[1], args[2]),
                        zip(api_items, image_batch, patch_results),
                    )
                )

            for orig, rows, cols in results:
                pooled_by_rows_batch.append(rows)
                pooled_by_columns_batch.append(cols)
        else:
            # For small batches, avoid threading overhead
            for item, image, patch_result in zip(api_items, image_batch, patch_results):
                orig, rows, cols = self.pool_single_image(item, image, patch_result)
                pooled_by_rows_batch.append(rows)
                pooled_by_columns_batch.append(cols)

        return original_batch, pooled_by_rows_batch, pooled_by_columns_batch

    def batch_embed_query(self, query_batch: List[str]) -> np.ndarray:
        """Embed a batch of queries using the API."""
        api_client = self._require_client()
        query_embeddings = api_client.embed_queries(query_batch)
        return np.array(query_embeddings[0]) if query_embeddings else np.array([])
