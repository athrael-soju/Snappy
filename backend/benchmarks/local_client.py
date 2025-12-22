"""Client for TomoroAI/tomoro-colqwen3-embed-4b model.

This module provides a local inference client for the Tomoro ColQwen3 embedding model
as an alternative to the remote ColPali service for benchmarking.
"""

from __future__ import annotations

import logging
import math
import threading
from typing import Any, Dict, List, Optional

import numpy as np
import torch
from PIL import Image

logger = logging.getLogger(__name__)

# Model configuration
MODEL_IDS = {
    "colqwen3-4b": "TomoroAI/tomoro-colqwen3-embed-4b",
    "colqwen3-8b": "TomoroAI/tomoro-colqwen3-embed-8b",
}
DEFAULT_MODEL_VARIANT = "colqwen3-4b"
DEFAULT_MAX_VISUAL_TOKENS = 1280
DEFAULT_DTYPE = torch.bfloat16


class TomoroColQwenClient:
    """Local inference client for Tomoro ColQwen3 embedding models.

    This client provides the same interface as ColPaliClient.generate_interpretability_maps()
    but runs inference locally using the Tomoro model.

    Supported model variants:
    - colqwen3-4b: TomoroAI/tomoro-colqwen3-embed-4b (faster, lower memory)
    - colqwen3-8b: TomoroAI/tomoro-colqwen3-embed-8b (higher quality)
    """

    def __init__(
        self,
        model_variant: str = DEFAULT_MODEL_VARIANT,
        model_id: Optional[str] = None,
        max_visual_tokens: int = DEFAULT_MAX_VISUAL_TOKENS,
        device: Optional[str] = None,
        dtype: torch.dtype = DEFAULT_DTYPE,
        use_flash_attention: bool = True,
    ):
        """Initialize the Tomoro ColQwen3 client.

        Args:
            model_variant: Model variant to use ('colqwen3-4b' or 'colqwen3-8b')
            model_id: Override HuggingFace model ID (takes precedence over model_variant)
            max_visual_tokens: Maximum number of visual tokens per image
            device: Device to run inference on (auto-detected if None)
            dtype: Model dtype (bfloat16 recommended)
            use_flash_attention: Whether to use flash attention 2
        """
        if model_id is not None:
            self.model_id = model_id
        elif model_variant in MODEL_IDS:
            self.model_id = MODEL_IDS[model_variant]
        else:
            raise ValueError(
                f"Unknown model variant: {model_variant}. "
                f"Supported variants: {list(MODEL_IDS.keys())}"
            )
        self.model_variant = model_variant
        self.max_visual_tokens = max_visual_tokens
        self.dtype = dtype
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.use_flash_attention = use_flash_attention

        self._model = None
        self._processor = None
        self._loaded = False
        # Thread lock for GPU inference - ensures only one thread uses the model at a time
        self._inference_lock = threading.Lock()

    def _ensure_loaded(self) -> None:
        """Lazily load the model and processor."""
        if self._loaded:
            return

        logger.info(
            "Loading Tomoro ColQwen3 model: %s (device=%s, dtype=%s)",
            self.model_id,
            self.device,
            self.dtype,
        )

        from transformers import AutoModel, AutoProcessor

        self._processor = AutoProcessor.from_pretrained(
            self.model_id,
            trust_remote_code=True,
            max_num_visual_tokens=self.max_visual_tokens,
        )

        attn_impl = "flash_attention_2" if self.use_flash_attention else "sdpa"
        try:
            self._model = AutoModel.from_pretrained(
                self.model_id,
                torch_dtype=self.dtype,
                attn_implementation=attn_impl,
                trust_remote_code=True,
                device_map=self.device,
            ).eval()
        except Exception as e:
            if self.use_flash_attention and "flash" in str(e).lower():
                logger.warning(
                    "Flash attention not available, falling back to SDPA: %s", e
                )
                self._model = AutoModel.from_pretrained(
                    self.model_id,
                    torch_dtype=self.dtype,
                    attn_implementation="sdpa",
                    trust_remote_code=True,
                    device_map=self.device,
                ).eval()
            else:
                raise

        self._loaded = True
        logger.info("Tomoro ColQwen3 model loaded successfully")

    def _encode_query(self, query: str) -> torch.Tensor:
        """Encode a text query into multi-vector embeddings.

        Args:
            query: The query text

        Returns:
            Query embeddings of shape (seq_len, embed_dim)
        """
        self._ensure_loaded()

        batch = self._processor.process_texts(texts=[query])
        batch = {k: v.to(self.device) for k, v in batch.items()}

        with torch.inference_mode():
            output = self._model(**batch)
            # embeddings shape: (batch=1, seq_len, embed_dim)
            embeddings = output.embeddings[0]  # (seq_len, embed_dim)

        return embeddings

    def _encode_image(self, image: Image.Image) -> Dict[str, Any]:
        """Encode an image into multi-vector embeddings.

        Args:
            image: PIL Image

        Returns:
            Dictionary containing:
            - embeddings: Image embeddings of shape (n_patches, embed_dim)
            - n_patches_x: Number of patches in x dimension
            - n_patches_y: Number of patches in y dimension
        """
        self._ensure_loaded()

        # Ensure RGB
        if image.mode != "RGB":
            image = image.convert("RGB")

        batch = self._processor.process_images(images=[image])
        batch = {
            k: v.to(self.device) if isinstance(v, torch.Tensor) else v
            for k, v in batch.items()
        }

        with torch.inference_mode():
            output = self._model(**batch)
            # embeddings shape: (batch=1, n_patches, embed_dim)
            embeddings = output.embeddings[0]  # (n_patches, embed_dim)

        # Calculate patch grid dimensions
        # The model uses a vision transformer that divides the image into patches
        # We need to figure out the patch grid size from the total number of patches
        n_patches = embeddings.shape[0]

        # The processor resizes images to fit within certain constraints
        # We estimate the patch grid based on aspect ratio
        aspect_ratio = image.width / image.height

        # Start with a reasonable estimate
        n_patches_y = int(math.sqrt(n_patches / aspect_ratio))
        n_patches_x = n_patches // n_patches_y

        # Adjust if the product doesn't match
        while n_patches_x * n_patches_y < n_patches:
            if aspect_ratio > 1:
                n_patches_x += 1
            else:
                n_patches_y += 1

        return {
            "embeddings": embeddings,
            "n_patches_x": n_patches_x,
            "n_patches_y": n_patches_y,
            "n_patches_total": n_patches,
        }

    def generate_interpretability_maps(
        self, query: str, image: Image.Image
    ) -> Dict[str, Any]:
        """Generate interpretability maps for a query-image pair.

        This method provides the same interface as ColPaliClient.generate_interpretability_maps()
        but uses the local Tomoro model.

        Thread-safe: Uses a lock to ensure only one inference runs at a time on the GPU.

        Args:
            query: The query text to interpret
            image: The document image to analyze

        Returns:
            Dictionary containing:
            - query: Original query text
            - tokens: List of query tokens
            - similarity_maps: Per-token similarity maps (list of 2D arrays)
            - n_patches_x: Number of patches in x dimension
            - n_patches_y: Number of patches in y dimension
            - image_width: Original image width
            - image_height: Original image height
        """
        # Acquire lock to ensure thread-safe GPU access
        with self._inference_lock:
            self._ensure_loaded()

            # Encode query and image
            query_embeddings = self._encode_query(query)  # (query_len, embed_dim)
            image_result = self._encode_image(image)
            image_embeddings = image_result["embeddings"]  # (n_patches, embed_dim)
            n_patches_x = image_result["n_patches_x"]
            n_patches_y = image_result["n_patches_y"]

            # Normalize embeddings for cosine similarity
            query_norm = torch.nn.functional.normalize(query_embeddings, p=2, dim=-1)
            image_norm = torch.nn.functional.normalize(image_embeddings, p=2, dim=-1)

            # Compute similarity: (query_len, n_patches)
            similarity = torch.matmul(query_norm, image_norm.T)

            # Convert to numpy and release GPU memory
            similarity_np = similarity.float().cpu().numpy()

            # Get query tokens for the response
            tokens = self._get_query_tokens(query)

        # Build per-token similarity maps
        similarity_maps = []
        for token_idx in range(similarity_np.shape[0]):
            token_scores = similarity_np[token_idx]

            # Reshape to 2D grid (pad if necessary)
            if len(token_scores) < n_patches_x * n_patches_y:
                padded = np.zeros(n_patches_x * n_patches_y)
                padded[: len(token_scores)] = token_scores
                token_scores = padded

            # Reshape to (n_patches_y, n_patches_x)
            sim_map = token_scores[: n_patches_x * n_patches_y].reshape(
                n_patches_y, n_patches_x
            )

            similarity_maps.append(
                {
                    "token": (
                        tokens[token_idx]
                        if token_idx < len(tokens)
                        else f"[{token_idx}]"
                    ),
                    "similarity_map": sim_map.tolist(),
                }
            )

        return {
            "query": query,
            "tokens": tokens,
            "similarity_maps": similarity_maps,
            "n_patches_x": n_patches_x,
            "n_patches_y": n_patches_y,
            "image_width": image.width,
            "image_height": image.height,
        }

    def _get_query_tokens(self, query: str) -> List[str]:
        """Get tokenized query for display purposes."""
        self._ensure_loaded()

        # Use the processor's tokenizer
        if hasattr(self._processor, "tokenizer"):
            tokenizer = self._processor.tokenizer
            token_ids = tokenizer.encode(query, add_special_tokens=False)
            tokens = [tokenizer.decode([tid]) for tid in token_ids]
            return tokens
        else:
            # Fallback: simple word split
            return query.split()

    def health_check(self) -> bool:
        """Check if the model can be loaded."""
        try:
            self._ensure_loaded()
            return True
        except Exception as e:
            logger.error("Tomoro model health check failed: %s", e)
            return False

    def get_info(self) -> Dict[str, Any]:
        """Get model information."""
        return {
            "model_variant": self.model_variant,
            "model_id": self.model_id,
            "device": self.device,
            "dtype": str(self.dtype),
            "max_visual_tokens": self.max_visual_tokens,
            "loaded": self._loaded,
        }
