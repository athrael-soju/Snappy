"""Embedding generation processor service."""

import base64
import io
import logging
from typing import List, cast

import numpy as np
import torch
from PIL import Image

from app.models.schemas import HeatmapResult, ImageEmbeddingItem
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

    def generate_heatmaps(
        self, query: str, images: List[Image.Image]
    ) -> List[HeatmapResult]:
        """Generate attention heatmaps for images given a query.

        Computes similarity maps between query tokens and image patches,
        aggregates them into a single heatmap, and overlays it on the original image.

        Args:
            query: The search query string
            images: List of PIL Images to generate heatmaps for

        Returns:
            List of HeatmapResult objects containing base64 encoded heatmap images
        """
        device = model_service.model.device
        results: List[HeatmapResult] = []

        with torch.no_grad():
            # Generate query embeddings
            batch_query = model_service.processor.process_queries([query]).to(device)
            query_embeddings = cast(
                torch.Tensor, model_service.model(**batch_query)
            )  # [1, query_seq, dim]

            for image in images:
                try:
                    # Process single image
                    batch_image = model_service.processor.process_images([image]).to(
                        device
                    )
                    image_embeddings = cast(
                        torch.Tensor, model_service.model(**batch_image)
                    )  # [1, img_seq, dim]

                    # Get number of patches for this image
                    n_patches_x, n_patches_y = model_service.processor.get_n_patches(
                        image_size=image.size,
                        patch_size=getattr(
                            model_service.model, "spatial_merge_size", None
                        ),
                    )

                    # Get image mask to identify image tokens
                    if hasattr(model_service.processor, "get_image_mask"):
                        image_mask = model_service.processor.get_image_mask(batch_image)
                    else:
                        # Fallback: use input_ids to create mask
                        input_ids = batch_image.get("input_ids")
                        if input_ids is not None:
                            image_mask = input_ids.eq(model_service.image_token_id)
                        else:
                            # Last resort: assume all tokens except first/last are image tokens
                            seq_len = image_embeddings.shape[1]
                            image_mask = torch.ones(1, seq_len, dtype=torch.bool)
                            image_mask[0, 0] = False
                            image_mask[0, -1] = False

                    # Compute similarity maps
                    heatmap_image = self._compute_and_overlay_heatmap(
                        query_embeddings=query_embeddings[0],  # [query_seq, dim]
                        image_embeddings=image_embeddings[0],  # [img_seq, dim]
                        image_mask=image_mask[0] if image_mask.dim() > 1 else image_mask,
                        n_patches_x=n_patches_x,
                        n_patches_y=n_patches_y,
                        original_image=image,
                    )

                    # Convert to base64
                    buffer = io.BytesIO()
                    heatmap_image.save(buffer, format="PNG")
                    buffer.seek(0)
                    heatmap_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

                    results.append(
                        HeatmapResult(
                            heatmap=heatmap_base64,
                            width=heatmap_image.width,
                            height=heatmap_image.height,
                        )
                    )
                except Exception as e:
                    logger.error(f"Failed to generate heatmap for image: {e}")
                    raise

        return results

    def _compute_and_overlay_heatmap(
        self,
        query_embeddings: torch.Tensor,
        image_embeddings: torch.Tensor,
        image_mask: torch.Tensor,
        n_patches_x: int,
        n_patches_y: int,
        original_image: Image.Image,
    ) -> Image.Image:
        """Compute similarity map and overlay as heatmap on the original image.

        Args:
            query_embeddings: Query token embeddings [query_seq, dim]
            image_embeddings: Image token embeddings [img_seq, dim]
            image_mask: Boolean mask for image tokens [img_seq]
            n_patches_x: Number of patches in x direction
            n_patches_y: Number of patches in y direction
            original_image: Original PIL image

        Returns:
            PIL Image with heatmap overlay
        """
        # Extract only image token embeddings
        if image_mask.sum() == 0:
            # No image tokens, return original
            return original_image

        image_token_embeddings = image_embeddings[image_mask]  # [n_img_tokens, dim]
        n_img_tokens = image_token_embeddings.shape[0]

        # Expected number of patches
        expected_patches = n_patches_x * n_patches_y

        # Handle case where we have global tokens (e.g., Idefics3 has extra 64 tokens)
        if n_img_tokens > expected_patches:
            # Use only the first expected_patches tokens (skip global tokens)
            image_token_embeddings = image_token_embeddings[:expected_patches]
        elif n_img_tokens < expected_patches:
            logger.warning(
                f"Fewer image tokens ({n_img_tokens}) than expected patches ({expected_patches})"
            )
            # Pad with zeros if needed
            padding = torch.zeros(
                expected_patches - n_img_tokens,
                image_token_embeddings.shape[1],
                device=image_token_embeddings.device,
                dtype=image_token_embeddings.dtype,
            )
            image_token_embeddings = torch.cat(
                [image_token_embeddings, padding], dim=0
            )

        # Reshape to patch grid [n_patches_y, n_patches_x, dim]
        patch_embeddings = image_token_embeddings.view(
            n_patches_y, n_patches_x, -1
        )

        # Normalize embeddings for cosine similarity
        patch_embeddings_norm = torch.nn.functional.normalize(
            patch_embeddings, p=2, dim=-1
        )
        query_embeddings_norm = torch.nn.functional.normalize(
            query_embeddings, p=2, dim=-1
        )

        # Compute similarity: [n_patches_y, n_patches_x, query_seq]
        similarity = torch.einsum(
            "yxd,qd->yxq", patch_embeddings_norm, query_embeddings_norm
        )

        # Aggregate across query tokens (max pooling to highlight strongest matches)
        aggregated_similarity = similarity.max(dim=-1).values  # [n_patches_y, n_patches_x]

        # Normalize to [0, 1]
        sim_min = aggregated_similarity.min()
        sim_max = aggregated_similarity.max()
        if sim_max - sim_min > 1e-6:
            normalized = (aggregated_similarity - sim_min) / (sim_max - sim_min)
        else:
            normalized = torch.zeros_like(aggregated_similarity)

        # Convert to numpy and resize to image dimensions
        heatmap_np = normalized.cpu().numpy()

        # Create heatmap image
        heatmap_resized = Image.fromarray(
            (heatmap_np * 255).astype(np.uint8)
        ).resize(original_image.size, Image.Resampling.BILINEAR)

        # Apply colormap (red for high attention, blue for low)
        heatmap_colored = self._apply_colormap(heatmap_resized)

        # Blend with original image
        original_rgb = original_image.convert("RGB")
        blended = Image.blend(original_rgb, heatmap_colored, alpha=0.4)

        return blended

    def _apply_colormap(self, grayscale_image: Image.Image) -> Image.Image:
        """Apply a colormap to a grayscale image.

        Uses a blue-to-red colormap where low values are blue and high values are red.

        Args:
            grayscale_image: Grayscale PIL image with values 0-255

        Returns:
            RGB PIL image with colormap applied
        """
        gray_np = np.array(grayscale_image).astype(np.float32) / 255.0

        # Create RGB arrays
        r = np.clip(gray_np * 2, 0, 1)  # Red increases with intensity
        g = np.clip(1 - np.abs(gray_np - 0.5) * 2, 0, 1)  # Green peaks at middle
        b = np.clip((1 - gray_np) * 2, 0, 1)  # Blue decreases with intensity

        # Stack and convert to uint8
        rgb = np.stack([r, g, b], axis=-1)
        rgb_uint8 = (rgb * 255).astype(np.uint8)

        return Image.fromarray(rgb_uint8, mode="RGB")


# Global embedding processor instance
embedding_processor = EmbeddingProcessor()
