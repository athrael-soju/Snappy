"""Pipeline processing components for document indexing.

This package provides generic pipeline components that are independent of
any specific vector database implementation.
"""

from .image_processor import ImageProcessor, ProcessedImage
from .storage import ImageStorageHandler
from .utils import log_stage_timing

__all__ = [
    "ImageProcessor",
    "ImageStorageHandler",
    "ProcessedImage",
    "log_stage_timing",
]
