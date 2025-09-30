"""Embedding and pooling operations for image processing."""

import numpy as np
from typing import List, Tuple
from PIL import Image
from concurrent.futures import ThreadPoolExecutor


class EmbeddingProcessor:
    """Handles embedding and pooling operations for images."""

    def __init__(self, api_client=None):
        """Initialize embedding processor.
        
        Args:
            api_client: ColPali client for embedding operations
        """
        self.api_client = api_client

    def get_patches(self, image_size: Tuple[int, int]) -> Tuple[int, int]:
        """Get number of patches for image using API."""
        width, height = image_size
        dimensions = [{"width": width, "height": height}]
        results = self.api_client.get_patches(dimensions)
        result = results[0]  # Get first (and only) result
        return result["n_patches_x"], result["n_patches_y"]

    @staticmethod
    def pool_image_tokens(
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

    def pool_single_image(self, item, image, patch_result):
        """Pool a single image's embeddings (for parallel execution)."""
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
        pooled_by_rows, pooled_by_columns = self.pool_image_tokens(
            image_embedding_np=image_embedding_np,
            start=int(start),
            patch_len=int(patch_len),
            x_patches=int(x_patches),
            y_patches=int(y_patches),
        )

        return image_embedding_np.tolist(), pooled_by_rows, pooled_by_columns

    def embed_and_mean_pool_batch(self, image_batch: List[Image.Image]):
        """
        Embed images via API and create mean pooled representations using explicit
        image-token boundaries provided by the API (no midpoint guessing).
        
        Pooling operations are parallelized for better CPU utilization on high-core-count systems.
        """
        # API returns per-image dicts: {embedding, image_patch_start, image_patch_len}
        api_items = self.api_client.embed_images(image_batch)

        # Batch get patches for all images
        dimensions = [
            {"width": image.size[0], "height": image.size[1]} for image in image_batch
        ]
        patch_results = self.api_client.get_patches(dimensions)

        # Parallelize pooling operations to maximize CPU utilization
        pooled_by_rows_batch = []
        pooled_by_columns_batch = []
        original_batch = []
        
        # For batches larger than 2, use parallel pooling
        if len(api_items) > 2:
            with ThreadPoolExecutor(max_workers=min(8, len(api_items))) as executor:
                results = list(executor.map(
                    lambda args: self.pool_single_image(args[0], args[1], args[2]),
                    zip(api_items, image_batch, patch_results)
                ))
                
            for orig, rows, cols in results:
                original_batch.append(orig)
                pooled_by_rows_batch.append(rows)
                pooled_by_columns_batch.append(cols)
        else:
            # For small batches, avoid threading overhead
            for item, image, patch_result in zip(api_items, image_batch, patch_results):
                orig, rows, cols = self.pool_single_image(item, image, patch_result)
                original_batch.append(orig)
                pooled_by_rows_batch.append(rows)
                pooled_by_columns_batch.append(cols)

        return original_batch, pooled_by_rows_batch, pooled_by_columns_batch

    def batch_embed_query(self, query_batch: List[str]) -> np.ndarray:
        """Embed query batch using API (returns the first, since we submit one)."""
        query_embeddings = self.api_client.embed_queries(
            query_batch
        )  # List[List[List[float]]]
        return np.array(query_embeddings[0]) if query_embeddings else np.array([])
