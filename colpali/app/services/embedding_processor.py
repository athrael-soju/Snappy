"""Embedding generation processor service."""

import io
import logging
from typing import List, Optional, Tuple, cast

import numpy as np
import torch
from PIL import Image

from app.models.schemas import ImageEmbeddingItem
from app.services.model_service import model_service

logger = logging.getLogger(__name__)


class EmbeddingProcessor:
    """Service for processing embeddings for queries and images."""

    def generate_query_embeddings(self, queries: List[str]) -> List[torch.Tensor]:
        """Generate embeddings for text queries.

        Args:
            queries: List of query strings to embed

        Returns:
            List of embedding tensors (one per query)
        """
        device = model_service.model.device
        with torch.no_grad():
            batch_query = model_service.processor.process_queries(queries).to(device)
            query_embeddings = cast(
                torch.Tensor, model_service.model(**batch_query)
            )  # [batch, seq, dim]
            # Unbind into per-sample tensors on CPU
            return list(torch.unbind(query_embeddings.to("cpu")))

    def generate_image_embeddings_with_boundaries(
        self, images: List[Image.Image]
    ) -> List[ImageEmbeddingItem]:
        """Generate embeddings for images and expose image-token boundaries.

        Args:
            images: List of PIL Images to embed

        Returns:
            List of ImageEmbeddingItem objects containing embeddings and token boundaries
        """
        device = model_service.model.device
        with torch.no_grad():
            # Tokenize / encode images
            batch_images = model_service.processor.process_images(images).to(device)

            # Forward pass
            image_embeddings = cast(
                torch.Tensor, model_service.model(**batch_images)
            )  # [batch, seq, dim]
            image_embeddings = image_embeddings.to("cpu")

            # Expect token ids to be present, so we can find image-token spans
            if "input_ids" not in batch_images:
                raise RuntimeError(
                    "Tokenizer output missing 'input_ids'; cannot compute image token boundaries."
                )

            input_ids = batch_images["input_ids"].to("cpu")  # [batch, seq]
            image_token_id = model_service.image_token_id

            batch_items: List[ImageEmbeddingItem] = []
            batch_size = input_ids.shape[0]

            for i in range(batch_size):
                ids = input_ids[i]  # [seq]
                emb = image_embeddings[i]  # [seq, dim]

                mask = ids.eq(image_token_id)  # bool mask for image tokens
                indices = torch.nonzero(mask, as_tuple=True)[
                    0
                ]  # [num_image_tokens] or []
                indices_list = (
                    indices.view(-1).tolist() if indices.numel() > 0 else []
                )

                if not indices_list:
                    # No image tokens found; return sentinel values
                    start = -1
                    length = 0
                else:
                    start = int(indices_list[0])
                    length = len(indices_list)

                batch_items.append(
                    ImageEmbeddingItem(
                        embedding=emb.tolist(),
                        image_patch_start=start,
                        image_patch_len=length,
                        image_patch_indices=[int(idx) for idx in indices_list],
                    )
                )

            return batch_items


    def generate_heatmap(
        self,
        query: str,
        image: Image.Image,
        alpha: float = 0.5,
    ) -> bytes:
        """Generate attention heatmap overlaid on the original image.

        Computes late interaction attention between query tokens and image patches,
        then creates a visual heatmap showing which image regions are most relevant.

        Args:
            query: The search query text
            image: The document page image
            alpha: Blending factor for heatmap overlay (0-1)

        Returns:
            PNG image bytes with heatmap overlaid on original image
        """
        device = model_service.model.device

        with torch.no_grad():
            # Process query and image
            batch_query = model_service.processor.process_queries([query]).to(device)
            batch_images = model_service.processor.process_images([image]).to(device)

            # Get embeddings
            query_embedding = cast(
                torch.Tensor, model_service.model(**batch_query)
            )  # [1, query_seq, dim]
            image_embedding = cast(
                torch.Tensor, model_service.model(**batch_images)
            )  # [1, image_seq, dim]

            # Get image patch boundaries
            if "input_ids" not in batch_images:
                raise RuntimeError(
                    "Tokenizer output missing 'input_ids'; cannot compute heatmap."
                )

            input_ids = batch_images["input_ids"][0]  # [seq]
            image_token_id = model_service.image_token_id
            mask = input_ids.eq(image_token_id)
            indices = torch.nonzero(mask, as_tuple=True)[0]

            if indices.numel() == 0:
                raise RuntimeError("No image tokens found in the processed image.")

            # Extract image patch embeddings
            start_idx = int(indices[0].item())
            num_patches = indices.numel()
            image_patch_emb = image_embedding[0, start_idx : start_idx + num_patches]  # [num_patches, dim]

            # Get patch grid dimensions
            n_patches_x, n_patches_y = self._get_patch_grid(image)

            # Compute attention scores via late interaction (MaxSim)
            # For each query token, find max similarity across all patches
            # Then sum across all query tokens to get per-patch importance
            query_emb = query_embedding[0]  # [query_seq, dim]

            # Normalize embeddings for cosine similarity
            query_norm = query_emb / (query_emb.norm(dim=-1, keepdim=True) + 1e-8)
            patch_norm = image_patch_emb / (image_patch_emb.norm(dim=-1, keepdim=True) + 1e-8)

            # Compute similarity: [query_seq, num_patches]
            similarity = torch.matmul(query_norm, patch_norm.T)

            # Sum similarities across query tokens to get patch importance
            # This gives us how much each patch contributes to the overall relevance
            patch_scores = similarity.sum(dim=0)  # [num_patches]

            # Convert to float32 before numpy (BFloat16 not supported by numpy)
            patch_scores = patch_scores.cpu().float().numpy()

        # Create heatmap image
        heatmap_bytes = self._create_heatmap_overlay(
            image, patch_scores, n_patches_x, n_patches_y, alpha
        )

        return heatmap_bytes

    def _get_patch_grid(self, image: Image.Image) -> Tuple[int, int]:
        """Get the patch grid dimensions for an image.

        Args:
            image: PIL Image

        Returns:
            Tuple of (n_patches_x, n_patches_y)
        """
        # Use get_n_patches if available
        if hasattr(model_service.processor, "get_n_patches"):
            get_n_patches_fn = model_service.processor.get_n_patches
            call_kwargs = {}

            # Get spatial_merge_size if needed
            spatial_merge_size = getattr(model_service.model, "spatial_merge_size", None)
            if spatial_merge_size is not None:
                # Check if function accepts patch_size or spatial_merge_size
                import inspect

                try:
                    sig = inspect.signature(get_n_patches_fn)
                    for name in sig.parameters:
                        if name in {"patch_size", "spatial_merge_size"}:
                            call_kwargs[name] = spatial_merge_size
                except (TypeError, ValueError):
                    pass

            n_patches_x, n_patches_y = get_n_patches_fn(image.size, **call_kwargs)
            return int(n_patches_x), int(n_patches_y)

        # Fallback: estimate from image sequence length
        # This is a rough estimate based on typical ViT configurations
        logger.warning("get_n_patches not available, using fallback estimation")
        return 16, 16

    def _create_heatmap_overlay(
        self,
        image: Image.Image,
        scores: np.ndarray,
        n_patches_x: int,
        n_patches_y: int,
        alpha: float,
    ) -> bytes:
        """Create heatmap overlay on the original image.

        Args:
            image: Original PIL Image
            scores: Flattened attention scores [num_patches]
            n_patches_x: Number of patches in x direction
            n_patches_y: Number of patches in y direction
            alpha: Blending factor (0-1)

        Returns:
            PNG image bytes
        """
        # Reshape scores to grid (x_patches, y_patches) -> (height, width)
        expected_patches = n_patches_x * n_patches_y
        actual_patches = len(scores)

        if actual_patches != expected_patches:
            logger.warning(
                f"Patch count mismatch: expected {expected_patches} "
                f"({n_patches_x}x{n_patches_y}), got {actual_patches}"
            )
            # Try to find best fit
            if actual_patches > 0:
                import math

                sqrt_patches = int(math.sqrt(actual_patches))
                for h in range(sqrt_patches, 0, -1):
                    if actual_patches % h == 0:
                        n_patches_y = h
                        n_patches_x = actual_patches // h
                        break

        # Reshape to (y, x) grid for image coordinates
        try:
            score_grid = scores.reshape(n_patches_y, n_patches_x)
        except ValueError:
            # If reshape fails, pad or truncate
            target_size = n_patches_y * n_patches_x
            if len(scores) < target_size:
                scores = np.pad(scores, (0, target_size - len(scores)), mode="constant")
            else:
                scores = scores[:target_size]
            score_grid = scores.reshape(n_patches_y, n_patches_x)

        # Normalize scores to [0, 1]
        score_min = score_grid.min()
        score_max = score_grid.max()
        if score_max > score_min:
            score_grid = (score_grid - score_min) / (score_max - score_min)
        else:
            score_grid = np.zeros_like(score_grid)

        # Resize heatmap to match image dimensions
        from PIL import ImageFilter

        heatmap_small = Image.fromarray((score_grid * 255).astype(np.uint8), mode="L")
        heatmap_resized = heatmap_small.resize(image.size, Image.Resampling.BILINEAR)

        # Apply Gaussian blur for smoother visualization
        heatmap_resized = heatmap_resized.filter(ImageFilter.GaussianBlur(radius=3))

        # Convert to numpy array
        heatmap_array = np.array(heatmap_resized, dtype=np.float32) / 255.0

        # Create colormap (blue -> green -> yellow -> red)
        # Using a custom viridis-like colormap
        def apply_colormap(values: np.ndarray) -> np.ndarray:
            """Apply a viridis-like colormap to normalized values."""
            # Simple plasma-like colormap: dark blue -> purple -> red -> yellow
            r = np.clip(values * 3 - 1, 0, 1)
            g = np.clip(values * 3 - 0.5, 0, 1) * np.clip(2 - values * 3, 0, 1)
            b = np.clip(1 - values * 2, 0, 1)

            # Make it more like a heat map (blue -> cyan -> green -> yellow -> red)
            r = np.where(values < 0.5, 0, (values - 0.5) * 2)
            g = np.where(values < 0.5, values * 2, 1 - (values - 0.5) * 2)
            b = np.where(values < 0.5, 1 - values * 2, 0)

            return np.stack([r, g, b], axis=-1)

        heatmap_rgb = apply_colormap(heatmap_array)
        heatmap_rgb = (heatmap_rgb * 255).astype(np.uint8)
        heatmap_image = Image.fromarray(heatmap_rgb, mode="RGB")

        # Blend with original image
        original_rgb = image.convert("RGB")
        blended = Image.blend(original_rgb, heatmap_image, alpha=alpha)

        # Convert to PNG bytes
        buffer = io.BytesIO()
        blended.save(buffer, format="PNG", optimize=True)
        buffer.seek(0)

        return buffer.getvalue()


# Global embedding processor instance
embedding_processor = EmbeddingProcessor()
