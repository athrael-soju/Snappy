"""Image storage helpers for pipeline processing."""

import base64
import logging
from typing import Any, Dict, List, Tuple

from PIL import Image
from .image_processor import ImageProcessor, ProcessedImage

logger = logging.getLogger(__name__)


class ImageStorageHandler:
    """Handles conversion of images to base64 for inline storage in Qdrant.

    Follows dependency injection principle - all dependencies must be provided.
    """

    def __init__(self, image_processor: ImageProcessor):
        """Initialize image storage handler.

        Args:
            image_processor: Image processor for format conversion (required)
        """
        self._image_processor = image_processor

    def store(
        self,
        batch_start: int,
        image_batch: List[Image.Image],
        meta_batch: List[dict],
        image_ids: List[str],
    ) -> Tuple[List[str], List[Dict[str, Any]], List[ProcessedImage]]:
        """
        Convert images to base64 for inline storage in Qdrant.

        Parameters
        ----------
        batch_start : int
            Starting index of this batch
        image_batch : List[Image.Image]
            Images to convert
        meta_batch : List[dict]
            Metadata for each image
        image_ids : List[str]
            Pre-generated image IDs (must be provided - generated during rasterization)

        Returns
        -------
        Tuple[List[str], List[Dict[str, Any]], List[ProcessedImage]]
            image_ids, image_records (with base64 data), and processed_images for reuse
        """

        # Process images once using centralized processor
        processed_images = self._image_processor.process_batch(image_batch)

        records: List[Dict[str, Any]] = []
        for idx, (image_id, processed) in enumerate(zip(image_ids, processed_images)):
            # Convert processed image to base64
            b64_data = base64.b64encode(processed.data).decode("utf-8")

            records.append(
                {
                    "image_data": b64_data,
                    "image_mime_type": processed.content_type,
                    "image_format": processed.format,
                    "image_size_bytes": processed.size,
                    "page_id": image_id,
                }
            )

        return image_ids, records, processed_images
