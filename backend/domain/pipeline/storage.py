"""Image processing helpers for pipeline - prepares images for inline Qdrant storage."""

import logging
from typing import Dict, List, Tuple

from PIL import Image

from .image_processor import ImageProcessor, ProcessedImage

logger = logging.getLogger(__name__)


class ImageStorageHandler:
    """Prepares images for inline storage in Qdrant payloads.

    Processes images and generates thumbnails for efficient search result display.
    All image data is stored as base64-encoded strings in Qdrant payloads.
    """

    def __init__(self, image_processor: ImageProcessor):
        """Initialize image storage handler.

        Args:
            image_processor: Image processor for format conversion and thumbnails
        """
        self._image_processor = image_processor

    def store(
        self,
        batch_start: int,
        image_batch: List[Image.Image],
        meta_batch: List[dict],
        image_ids: List[str],
    ) -> Tuple[List[str], List[Dict[str, object]], List[ProcessedImage]]:
        """
        Process images for inline storage in Qdrant.

        Parameters
        ----------
        batch_start : int
            Starting index of this batch
        image_batch : List[Image.Image]
            Images to process
        meta_batch : List[dict]
            Metadata for each image
        image_ids : List[str]
            Pre-generated image IDs

        Returns
        -------
        Tuple[List[str], List[Dict[str, object]], List[ProcessedImage]]
            image_ids, image_records (with inline data), and processed_images
        """
        # Process images and create thumbnails in one pass
        full_images, thumbnails = self._image_processor.process_batch_with_thumbnails(
            image_batch
        )

        records: List[Dict[str, object]] = []
        for idx, image_id in enumerate(image_ids):
            full_img = full_images[idx]
            thumb = thumbnails[idx]

            records.append(
                {
                    "page_id": image_id,
                    "image_inline": True,
                    "image_storage": "qdrant",
                    # Thumbnail for search results (smaller, faster to transfer)
                    "image_data": thumb.to_base64(),
                    "image_mime_type": thumb.content_type,
                    "image_format": thumb.format,
                    "image_size_bytes": thumb.size,
                    "image_width": thumb.width,
                    "image_height": thumb.height,
                    # Full image data for detailed view
                    "image_data_full": full_img.to_base64(),
                    "image_full_size_bytes": full_img.size,
                    "image_full_width": full_img.width,
                    "image_full_height": full_img.height,
                }
            )

        logger.debug(
            f"Processed {len(image_batch)} images for inline storage "
            f"(batch starting at {batch_start})"
        )

        return image_ids, records, full_images
