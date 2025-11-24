"""Image storage helpers for pipeline processing."""

import logging
from typing import Dict, List, Tuple

from PIL import Image
from .image_processor import ImageProcessor, ProcessedImage

logger = logging.getLogger(__name__)


class ImageStorageHandler:
    """Handles persistence of image batches in MinIO.

    Follows dependency injection principle - all dependencies must be provided.
    """

    def __init__(self, minio_service, image_processor: ImageProcessor):
        """Initialize image storage handler.

        Args:
            minio_service: MinIO service for object storage
            image_processor: Image processor for format conversion (required)
        """
        self._minio_service = minio_service
        self._image_processor = image_processor

    def store(
        self,
        batch_start: int,
        image_batch: List[Image.Image],
        meta_batch: List[dict],
        image_ids: List[str],
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
            Metadata for each image, must contain 'document_id' and 'page_number'
        image_ids : List[str]
            Pre-generated image IDs (must be provided - generated during rasterization)

        Returns
        -------
        Tuple[List[str], List[Dict[str, object]], List[ProcessedImage]]
            image_ids, image_records, and processed_images for reuse
        """

        if self._minio_service is None:
            raise Exception(
                "MinIO service is not configured; it is required for image storage."
            )

        # Extract required fields from metadata - will raise KeyError if missing
        document_ids = []
        page_numbers = []
        for meta in meta_batch:
            try:
                document_id = meta["document_id"]
                page_num = meta["page_number"]
            except KeyError as exc:
                raise ValueError(
                    f"Metadata missing required field {exc} for hierarchical storage. Got: {meta}"
                ) from exc
            document_ids.append(document_id)
            page_numbers.append(page_num)

        # Process images once using centralized processor
        processed_images = self._image_processor.process_batch(image_batch)

        try:
            # Store pre-processed images in MinIO with batch-size parallelism
            # Batch size controls parallelism across all stages
            image_url_map = self._minio_service.store_processed_images_batch(
                processed_images,
                image_ids=image_ids,
                document_ids=document_ids,
                page_numbers=page_numbers,
                max_workers=len(image_batch),  # Use batch size for parallelism
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
                    "page_id": image_id,
                }
            )

        return image_ids, records, processed_images
