"""Embedding generation processor service."""

import logging
from typing import List, cast

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


# Global embedding processor instance
embedding_processor = EmbeddingProcessor()
