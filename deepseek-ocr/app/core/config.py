"""
Configuration management for DeepSeek OCR service.
"""

from typing import Any, Dict

import torch
from decouple import config as env_config


class Settings:
    """Application settings."""

    # API Configuration
    API_HOST: str = env_config("API_HOST", default="0.0.0.0")
    API_PORT: int = env_config("API_PORT", default=8200, cast=int)

    # Model Configuration
    MODEL_NAME: str = env_config("MODEL_NAME", default="deepseek-ai/DeepSeek-OCR")
    DEVICE: str = env_config(
        "DEVICE", default="cuda" if torch.cuda.is_available() else "cpu"
    )
    TORCH_DTYPE = torch.bfloat16 if DEVICE == "cuda" else torch.float32

    # CORS Configuration
    ALLOWED_ORIGINS: str = env_config("ALLOWED_ORIGINS", default="*")

    # Model Processing Configurations
    MODEL_CONFIGS: Dict[str, Dict[str, Any]] = {
        "Gundam": {"base_size": 1024, "image_size": 640, "crop_mode": True},
        "Tiny": {"base_size": 512, "image_size": 512, "crop_mode": False},
        "Small": {"base_size": 640, "image_size": 640, "crop_mode": False},
        "Base": {"base_size": 1024, "image_size": 1024, "crop_mode": False},
        "Large": {"base_size": 1280, "image_size": 1280, "crop_mode": False},
    }

    # Task Prompts
    TASK_PROMPTS: Dict[str, Dict[str, Any]] = {
        "markdown": {
            "prompt": "<image>\n<|grounding|>Convert the document to markdown.",
            "has_grounding": True,
        },
        "plain_ocr": {
            "prompt": "<image>\nFree OCR.",
            "has_grounding": False,
        },
        "locate": {
            "prompt": "<image>\nLocate <|ref|>{text}<|/ref|> in the image.",
            "has_grounding": True,
        },
        "describe": {
            "prompt": "<image>\nDescribe this image in detail.",
            "has_grounding": False,
        },
        "custom": {
            "prompt": "",
            "has_grounding": False,
        },
    }


settings = Settings()
