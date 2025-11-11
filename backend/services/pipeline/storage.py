"""Image storage helpers for pipeline processing."""

import logging
import uuid
from typing import Dict, List, Tuple

import config
from PIL import Image
from services.image_processor import ImageProcessor, ProcessedImage

logger = logging.getLogger(__name__)


class ImageStorageHandler:
    """Handles persistence of image batches in MinIO."""

    def __init__(self, minio_service, image_processor: ImageProcessor | None = None):
        self._minio_service = minio_service
        # Create processor with config defaults if not provided
        if image_processor is None:
            image_processor = ImageProcessor(
                default_format=config.IMAGE_FORMAT,
                default_quality=config.IMAGE_QUALITY,
            )
        self._image_processor = image_processor

    def store(
        self,
        batch_start: int,
        image_batch: List[Image.Image],
        meta_batch: List[dict],
    ) -> Tuple[List[str], List[Dict[str, object]], List[ProcessedImage]]:
        """
        Store images in MinIO using hierarchical structure.

        Parameters
        ----------
        batch_start : int
            Starting index of this batch
        image_batch : List[Image.Image]
            Images to store
        meta_batch : List[dict]
            Metadata for each image, must contain 'filename' and 'page_number'

        Returns
        -------
        Tuple[List[str], List[Dict[str, object]], List[ProcessedImage]]
            image_ids, image_records, and processed_images for reuse
        """
        image_ids = [str(uuid.uuid4()) for _ in image_batch]

        if self._minio_service is None:
            raise Exception(
                "MinIO service is not configured; it is required for image storage."
            )

        # Extract filenames and page_numbers from metadata
        filenames = []
        page_numbers = []
        for meta in meta_batch:
            filename = meta.get("filename")
            page_num = meta.get("page_number")
            if filename is None or page_num is None:
                raise ValueError(
                    f"Metadata must contain 'filename' and 'page_number' for hierarchical storage. Got: {meta}"
                )
            filenames.append(filename)
            page_numbers.append(page_num)

        # Process images once using centralized processor
        processed_images = self._image_processor.process_batch(image_batch)

        try:
            # Store pre-processed images in MinIO
            image_url_map = self._minio_service.store_processed_images_batch(
                processed_images,
                image_ids=image_ids,
                filenames=filenames,
                page_numbers=page_numbers,
            )
        except Exception as exc:
            raise Exception(
                f"Error storing images in MinIO for batch starting at {batch_start}: {exc}"
            ) from exc

        records: List[Dict[str, object]] = []
        for idx, image_id in enumerate(image_ids):
            image_url = image_url_map.get(image_id)
            if image_url is None:
                raise Exception(
                    f"Image upload failed for batch starting at {batch_start}: missing URL for {image_id}"
                )
            # Attach URL to processed image for downstream use (e.g., OCR storage)
            if idx < len(processed_images):
                processed_images[idx].url = image_url

            records.append(
                {
                    "image_url": image_url,
                    "image_inline": False,
                    "image_storage": "minio",
                }
            )

        return image_ids, records, processed_images
