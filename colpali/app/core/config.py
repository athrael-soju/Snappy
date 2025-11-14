"""Configuration settings for ColPali service."""

import os
from typing import Literal

import torch


class Settings:
    """Application settings loaded from environment variables."""

    def __init__(self):
        # Model configuration
        self.MODEL_ID: str = os.getenv(
            "COLPALI_MODEL_ID", "ModernVBERT/colmodernvbert-merged"
        )
        self.API_VERSION: str = os.getenv("COLPALI_API_VERSION", "0.0.2")

        # CPU parallelism configuration
        self.CPU_THREADS: int = int(os.getenv("CPU_THREADS", "4"))
        self.ENABLE_CPU_MULTIPROCESSING: bool = (
            os.getenv("ENABLE_CPU_MULTIPROCESSING", "false").lower() == "true"
        )

        # Device detection
        self.device: Literal["cuda:0", "mps", "cpu"] = (
            "cuda:0"
            if torch.cuda.is_available()
            else "mps"
            if torch.backends.mps.is_available()
            else "cpu"
        )

        # Configure CPU threading for better performance
        if self.device == "cpu":
            torch.set_num_threads(self.CPU_THREADS)
            torch.set_num_interop_threads(self.CPU_THREADS)

        # Torch dtype based on device
        self.TORCH_DTYPE = torch.bfloat16 if self.device != "cpu" else torch.float32


# Global settings instance
settings = Settings()
