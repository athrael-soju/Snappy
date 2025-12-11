"""Model loading and management service."""

import logging
from typing import Any, cast

import torch
from transformers import AutoModel, AutoProcessor
from transformers.utils.import_utils import is_flash_attn_2_available

from app.core.config import settings

logger = logging.getLogger(__name__)


class ModelService:
    """Service for managing the ColQwen3 model and processor."""

    def __init__(self):
        """Initialize the model service."""
        self.model: Any = None
        self.processor: Any = None
        self.image_token_id: int = 0

    def load_model(self):
        """Load the ColQwen3 model and processor."""
        logger.info(f"Loading model: {settings.MODEL_ID}")
        logger.info(f"Device: {settings.device}")
        logger.info(f"Torch dtype: {settings.TORCH_DTYPE}")

        # Load processor first (needed for max_num_visual_tokens)
        self.processor = cast(
            Any,
            AutoProcessor.from_pretrained(
                settings.MODEL_ID,
                trust_remote_code=True,
                max_num_visual_tokens=settings.MAX_NUM_VISUAL_TOKENS,
            ),
        )

        # Load model
        attn_impl = "flash_attention_2" if is_flash_attn_2_available() else None
        self.model = cast(
            Any,
            AutoModel.from_pretrained(
                settings.MODEL_ID,
                torch_dtype=settings.TORCH_DTYPE,
                device_map=settings.device,
                attn_implementation=attn_impl,
                trust_remote_code=True,
            ).eval(),
        )

        # Resolve image token ID
        self.image_token_id = self._resolve_image_token_id()

        logger.info(f"Model loaded successfully on device: {self.model.device}")
        logger.info(f"Model dtype: {self.model.dtype}")
        logger.info(
            f"Flash Attention 2: {'enabled' if is_flash_attn_2_available() else 'disabled'}"
        )
        logger.info(f"Image token ID: {self.image_token_id}")
        logger.info(f"Max visual tokens: {settings.MAX_NUM_VISUAL_TOKENS}")

        # Log CPU threading configuration if applicable
        if settings.device == "cpu":
            logger.info(f"CPU mode: Set torch threads to {settings.CPU_THREADS}")

    def _resolve_image_token_id(self) -> int:
        """Best-effort resolution of the image token id for the current processor."""
        if hasattr(self.processor, "image_token_id"):
            return int(self.processor.image_token_id)  # type: ignore[arg-type]

        image_token = getattr(self.processor, "image_token", None)
        if image_token is not None and hasattr(self.processor, "tokenizer"):
            token_id = self.processor.tokenizer.convert_tokens_to_ids(image_token)  # type: ignore[attr-defined]
            if token_id is not None:
                return int(token_id)

        raise AttributeError("Processor does not expose an image_token_id.")

    def get_model_info(self) -> dict[str, Any]:
        """Get information about the loaded model."""
        spatial_merge_size = getattr(self.model, "spatial_merge_size", None)
        image_seq_len = getattr(self.processor, "image_seq_len", None)

        return {
            "version": settings.API_VERSION,
            "model_id": settings.MODEL_ID,
            "device": str(self.model.device),
            "dtype": str(self.model.dtype),
            "flash_attn": is_flash_attn_2_available(),
            "spatial_merge_size": spatial_merge_size,
            "dim": getattr(self.model, "dim", None),
            "image_token_id": self.image_token_id,
            "image_seq_len": image_seq_len,
        }


# Global model service instance
model_service = ModelService()
