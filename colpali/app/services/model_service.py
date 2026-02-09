"""Model loading and management service."""

import logging
from typing import Any, Tuple, Union, cast

from app.core.config import settings
from transformers.utils.import_utils import is_flash_attn_2_available

logger = logging.getLogger(__name__)


def _resolve_model_classes(model_id: str) -> Tuple[Any, Any]:
    """Resolve the correct model and processor classes based on model ID."""
    model_id_lower = model_id.lower()

    if "modernvbert" in model_id_lower:
        from colpali_engine.models import ColModernVBert, ColModernVBertProcessor
        return ColModernVBert, ColModernVBertProcessor
    else:
        from colpali_engine.models import ColQwen3, ColQwen3Processor
        return ColQwen3, ColQwen3Processor


class ModelService:
    """Service for managing the ColPali embedding model and processor."""

    def __init__(self):
        """Initialize the model service."""
        self.model: Any = None
        self.processor: Any = None
        self.image_token_id: int = 0

    def load_model(self):
        """Load the embedding model and processor."""
        logger.info(f"Loading model: {settings.MODEL_ID}")
        logger.info(f"Device: {settings.device}")
        logger.info(f"Torch dtype: {settings.TORCH_DTYPE}")

        ModelClass, ProcessorClass = _resolve_model_classes(settings.MODEL_ID)
        logger.info(f"Using model class: {ModelClass.__name__}")

        # Load model
        self.model = cast(
            Any,
            ModelClass.from_pretrained(
                settings.MODEL_ID,
                torch_dtype=settings.TORCH_DTYPE,
                device_map=settings.device,
                attn_implementation=(
                    "flash_attention_2" if is_flash_attn_2_available() else None
                ),
                trust_remote_code=True,
            ).eval(),
        )

        # Load processor
        _processor_loaded: Union[Any, Tuple[Any, dict[str, Any]]] = (
            ProcessorClass.from_pretrained(
                settings.MODEL_ID, trust_remote_code=True
            )
        )

        if isinstance(_processor_loaded, tuple):
            self.processor = cast(Any, _processor_loaded[0])
        else:
            self.processor = cast(Any, _processor_loaded)

        # Resolve image token ID
        self.image_token_id = self._resolve_image_token_id()

        logger.info(f"Model loaded successfully on device: {self.model.device}")
        logger.info(f"Model dtype: {self.model.dtype}")
        logger.info(
            f"Flash Attention 2: {'enabled' if is_flash_attn_2_available() else 'disabled'}"
        )
        logger.info(f"Image token ID: {self.image_token_id}")

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
