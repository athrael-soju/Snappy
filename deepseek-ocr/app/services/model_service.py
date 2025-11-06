"""
DeepSeek OCR model service for loading and inference.
"""

import os
import shutil
import sys
import tempfile
from io import StringIO
from typing import Any, Dict, Optional

from app.core.config import settings
from app.core.logging import logger
from PIL import Image, ImageOps
from transformers import AutoModel, AutoTokenizer


class ModelService:
    """Service for managing DeepSeek OCR model."""

    def __init__(self):
        """Initialize model service."""
        self.tokenizer: Optional[AutoTokenizer] = None
        self.model: Optional[AutoModel] = None
        self._initialized = False

    def load_model(self):
        """Load the DeepSeek OCR model and tokenizer."""
        if self._initialized:
            logger.info("Model already loaded")
            return

        logger.info("=" * 60)
        logger.info("DeepSeek OCR Model Loading")
        logger.info("=" * 60)
        logger.info(f"Model: {settings.MODEL_NAME}")
        logger.info(f"Device: {settings.DEVICE.upper()}")
        logger.info(f"Dtype: {settings.TORCH_DTYPE}")

        # Check CUDA availability
        import torch

        if torch.cuda.is_available():
            logger.info(f"CUDA Device: {torch.cuda.get_device_name(0)}")
            logger.info(f"CUDA Version: {torch.version.cuda}")

        using_flash_attn = settings.DEVICE == "cuda"
        logger.info(
            f"Flash Attention 2: {'ENABLED' if using_flash_attn else 'DISABLED (CPU mode)'}"
        )
        logger.info("=" * 60)

        try:
            self.tokenizer = AutoTokenizer.from_pretrained(
                settings.MODEL_NAME, trust_remote_code=True
            )

            model_kwargs = {
                "trust_remote_code": True,
                "use_safetensors": True,
            }

            # Only use flash attention on CUDA
            if settings.DEVICE == "cuda":
                model_kwargs["_attn_implementation"] = "flash_attention_2"
                model_kwargs["torch_dtype"] = settings.TORCH_DTYPE

            self.model = AutoModel.from_pretrained(settings.MODEL_NAME, **model_kwargs)
            self.model = self.model.eval()

            if settings.DEVICE == "cuda":
                self.model = self.model.cuda()

            self._initialized = True
            logger.info("✓ Model loaded successfully")
            logger.info("=" * 60)

        except Exception as e:
            logger.error(f"✗ Failed to load model: {e}")
            raise

    def is_loaded(self) -> bool:
        """Check if model is loaded."""
        return self._initialized and self.model is not None

    def infer(
        self,
        image: Image.Image,
        prompt: str,
        base_size: int,
        image_size: int,
        crop_mode: bool,
    ) -> str:
        """
        Run inference on an image.

        Args:
            image: PIL Image to process
            prompt: Text prompt for the model
            base_size: Base size for processing
            image_size: Image size for processing
            crop_mode: Whether to use crop mode

        Returns:
            Raw model output text
        """
        if not self.is_loaded():
            raise RuntimeError("Model not loaded. Call load_model() first.")

        # Ensure RGB format
        if image.mode in ("RGBA", "LA", "P"):
            image = image.convert("RGB")
        image = ImageOps.exif_transpose(image)

        # Save image to temporary file
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
        image.save(tmp.name, "JPEG", quality=95)
        tmp.close()
        out_dir = tempfile.mkdtemp()

        try:
            # Capture stdout to get model output
            stdout = sys.stdout
            sys.stdout = StringIO()

            # Run inference
            self.model.infer(
                tokenizer=self.tokenizer,
                prompt=prompt,
                image_file=tmp.name,
                output_path=out_dir,
                base_size=base_size,
                image_size=image_size,
                crop_mode=crop_mode,
            )

            # Filter output
            result = "\n".join(
                [
                    line
                    for line in sys.stdout.getvalue().split("\n")
                    if not any(
                        s in line
                        for s in [
                            "image:",
                            "other:",
                            "PATCHES",
                            "====",
                            "BASE:",
                            "%|",
                            "torch.Size",
                        ]
                    )
                ]
            ).strip()

            sys.stdout = stdout

            return result

        finally:
            # Cleanup
            try:
                os.unlink(tmp.name)
            except OSError:
                pass
            try:
                shutil.rmtree(out_dir, ignore_errors=True)
            except Exception:
                pass

    def get_model_info(self) -> Dict[str, Any]:
        """Get model information."""
        return {
            "model": settings.MODEL_NAME,
            "device": settings.DEVICE,
            "dtype": str(settings.TORCH_DTYPE),
            "loaded": self.is_loaded(),
        }


# Global model service instance
model_service = ModelService()
