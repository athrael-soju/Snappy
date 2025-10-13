"""Embedding and pooling operations for image processing."""

import importlib
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import TYPE_CHECKING, Any, List, Optional, Tuple, cast

import numpy as np
from PIL import Image

if TYPE_CHECKING:
    from services.colpali import ColPaliService

    from backend import config as config  # type: ignore
else:  # pragma: no cover - runtime import for application execution
    import config  # type: ignore

MuveraLike = Any

logger = logging.getLogger(__name__)


class EmbeddingProcessor:
    """Handles embedding and pooling operations for images."""

    def __init__(self, api_client: Optional["ColPaliService"] = None) -> None:
        """Initialize embedding processor.

        Args:
            api_client: ColPali client for embedding operations
        """
        self.api_client = api_client

    def _require_client(self) -> "ColPaliService":
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
    ) -> Tuple[List[List[float]], List[List[float]]]:
        """Mean-pool image tokens by rows and columns, preserving prefix/postfix tokens."""
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
        )

        return image_embedding_np.tolist(), pooled_by_rows, pooled_by_columns

    def embed_and_mean_pool_batch(self, image_batch: List[Image.Image]):
        """Embed images via API and optionally perform mean pooling."""
        api_client = self._require_client()
        # API returns per-image dicts: {embedding, image_patch_start, image_patch_len}
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


class MuveraPostprocessor:
    """Wrapper around fastembed.postprocess.Muvera."""

    def __init__(self, input_dim: int) -> None:
        self.enabled = bool(config.MUVERA_ENABLED)
        self._muvera: Optional[MuveraLike] = None
        self._embedding_size: Optional[int] = None

        if not self.enabled:
            logger.info("MUVERA disabled via config; postprocessor will not be used")
            return

        try:
            module = importlib.import_module("fastembed.postprocess")
            muvera_cls = getattr(module, "Muvera")

            k_sim = int(config.MUVERA_K_SIM)
            dim_proj = int(config.MUVERA_DIM_PROJ)
            r_reps = int(config.MUVERA_R_REPS)
            random_seed = int(config.MUVERA_RANDOM_SEED)

            muvera = muvera_cls(
                dim=input_dim,
                k_sim=k_sim,
                dim_proj=dim_proj,
                r_reps=r_reps,
                random_seed=random_seed,
            )
            self._muvera = muvera
            self._embedding_size = int(muvera.embedding_size)
            logger.info(
                "Initialized MUVERA: input_dim=%s, k_sim=%s, dim_proj=%s, r_reps=%s, fde_dim=%s",
                input_dim,
                k_sim,
                dim_proj,
                r_reps,
                self._embedding_size,
            )
        except Exception as exc:  # pragma: no cover - best effort
            logger.error("Failed to initialize MUVERA: %s", exc)
            self.enabled = False
            self._muvera = None
            self._embedding_size = None

    @property
    def embedding_size(self) -> Optional[int]:
        return self._embedding_size

    def _require_impl(self) -> MuveraLike:
        if not self.enabled or self._muvera is None:
            raise RuntimeError("MUVERA postprocessor is not available")
        return self._muvera

    def process_document(
        self, multivectors: List[List[float]]
    ) -> Optional[List[float]]:
        if not multivectors:
            logger.debug("MUVERA.process_document received empty multivectors")
            return None
        try:
            muvera = self._require_impl()
        except RuntimeError:
            return None
        arr = np.asarray(multivectors, dtype=np.float32)
        logger.debug("MUVERA.process_document input shape: %s", arr.shape)
        fde = muvera.process_document(arr)
        out = cast(np.ndarray, fde).astype(np.float32).tolist()
        logger.debug("MUVERA.process_document output length: %d", len(out))
        return out

    def process_query(self, multivectors: List[List[float]]) -> Optional[List[float]]:
        if not multivectors:
            logger.debug("MUVERA.process_query received empty multivectors")
            return None
        try:
            muvera = self._require_impl()
        except RuntimeError:
            return None
        arr = np.asarray(multivectors, dtype=np.float32)
        logger.debug("MUVERA.process_query input shape: %s", arr.shape)
        fde = muvera.process_query(arr)
        out = cast(np.ndarray, fde).astype(np.float32).tolist()
        logger.debug("MUVERA.process_query output length: %d", len(out))
        return out
