"""Embedding generation processor service."""

import logging
from typing import Any, List, Optional, cast

import torch
from PIL import Image

from app.models.schemas import ImageEmbeddingItem, InterpretabilityResponse, TokenSimilarityMap
from app.services.model_service import model_service

logger = logging.getLogger(__name__)


def _get_spatial_merge_size() -> Optional[int]:
    """Get spatial_merge_size from model or its config."""
    value = getattr(model_service.model, "spatial_merge_size", None)
    if value is None:
        vision_config = getattr(
            getattr(model_service.model, "config", None), "vision_config", None
        )
        if vision_config is not None:
            value = getattr(vision_config, "spatial_merge_size", None)
    return value


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
            batch_query = model_service.processor.process_texts(texts=queries)
            batch_query = {
                k: v.to(device) if isinstance(v, torch.Tensor) else v
                for k, v in batch_query.items()
            }
            output = model_service.model(**batch_query)
            # Model returns output with .embeddings property
            query_embeddings = cast(torch.Tensor, output.embeddings)  # [batch, seq, dim]
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
            batch_images = model_service.processor.process_images(images=images)
            batch_images = {
                k: v.to(device) if isinstance(v, torch.Tensor) else v
                for k, v in batch_images.items()
            }

            # Forward pass
            output = model_service.model(**batch_images)
            # Model returns output with .embeddings property
            image_embeddings = cast(torch.Tensor, output.embeddings)  # [batch, seq, dim]
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

    def generate_interpretability_maps(
        self, query: str, image: Image.Image
    ) -> InterpretabilityResponse:
        """Generate interpretability maps showing query-document token correspondence.

        Args:
            query: The query text to interpret
            image: The document image to analyze

        Returns:
            InterpretabilityResponse with per-token similarity maps
        """
        device = model_service.model.device

        with torch.no_grad():
            # Process query and image (keep original BatchFeature for get_image_mask)
            batch_query_raw = model_service.processor.process_texts(texts=[query])
            batch_query = {
                k: v.to(device) if isinstance(v, torch.Tensor) else v
                for k, v in batch_query_raw.items()
            }
            batch_images_raw = model_service.processor.process_images(images=[image])
            batch_images = {
                k: v.to(device) if isinstance(v, torch.Tensor) else v
                for k, v in batch_images_raw.items()
            }

            # Generate embeddings
            query_output = model_service.model(**batch_query)
            query_embeddings = cast(
                torch.Tensor, query_output.embeddings
            )  # [1, seq, dim]
            image_output = model_service.model(**batch_images)
            image_embeddings = cast(
                torch.Tensor, image_output.embeddings
            )  # [1, seq, dim]

            # Get number of patches for the image
            spatial_merge_size = _get_spatial_merge_size()
            n_patches = model_service.processor.get_n_patches(
                (image.size[1], image.size[0]),
                spatial_merge_size=spatial_merge_size,
            )  # (height, width) -> (n_patches_x, n_patches_y)

            # Get image mask (use raw BatchFeature which has .input_ids attribute)
            image_mask = model_service.processor.get_image_mask(batch_images_raw)

            # Compute similarity maps manually
            # Extract image patch embeddings using mask
            mask = image_mask[0]  # [seq]
            image_patch_embeddings = image_embeddings[0][mask]  # [n_patches, dim]

            # Normalize embeddings for cosine similarity
            query_norm = torch.nn.functional.normalize(query_embeddings[0], dim=-1)
            image_norm = torch.nn.functional.normalize(image_patch_embeddings, dim=-1)

            # Compute similarity: [query_seq, n_patches]
            similarities = torch.matmul(query_norm, image_norm.T)

            # Reshape to [query_seq, n_patches_x, n_patches_y]
            n_patches_x, n_patches_y = n_patches
            similarity_maps = similarities.view(-1, n_patches_x, n_patches_y)

            # Extract query tokens (filtering out special tokens)
            input_ids = batch_query_raw["input_ids"][0].tolist()
            query_tokens = model_service.processor.tokenizer.convert_ids_to_tokens(
                batch_query_raw["input_ids"][0]
            )
            special_token_ids = set(
                model_service.processor.tokenizer.all_special_ids or []
            )

            # Filter tokens and their corresponding similarity maps
            filtered_token_maps: List[TokenSimilarityMap] = []

            for idx, (token, token_id) in enumerate(zip(query_tokens, input_ids)):
                if token_id in special_token_ids:
                    continue

                # Get the similarity map for this token using idx (not a separate counter)
                # similarity_maps includes ALL tokens, so we use idx to get the correct map
                token_sim_map = similarity_maps[idx].cpu().tolist()

                # Clean token for display (remove special characters)
                display_token = token.replace("Ġ", " ").replace("▁", " ")

                filtered_token_maps.append(
                    TokenSimilarityMap(
                        token=display_token,
                        token_index=idx,
                        similarity_map=token_sim_map,
                    )
                )

            # Extract just the token strings for the response
            filtered_tokens = [tm.token for tm in filtered_token_maps]

            return InterpretabilityResponse(
                query=query,
                tokens=filtered_tokens,
                similarity_maps=filtered_token_maps,
                n_patches_x=int(n_patches[0]),
                n_patches_y=int(n_patches[1]),
                image_width=image.size[0],
                image_height=image.size[1],
            )


# Global embedding processor instance
embedding_processor = EmbeddingProcessor()
