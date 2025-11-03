"""Image storage helpers for Qdrant indexing."""

import logging
import uuid
from typing import Dict, List, Tuple

import config
from PIL import Image

logger = logging.getLogger(__name__)


class ImageStorageHandler:
    """Handles persistence of image batches in MinIO."""

    def __init__(self, minio_service):
        self._minio_service = minio_service

    def store(
        self,
        batch_start: int,
        image_batch: List[Image.Image],
    ) -> Tuple[List[str], List[Dict[str, object]]]:
        image_ids = [str(uuid.uuid4()) for _ in image_batch]

        if self._minio_service is None:
            raise Exception(
                "MinIO service is not configured; it is required for image storage."
            )

        try:
            image_url_map = self._minio_service.store_images_batch(
                image_batch,
                image_ids=image_ids,
                quality=config.IMAGE_QUALITY,
            )
        except Exception as exc:
            raise Exception(
                f"Error storing images in MinIO for batch starting at {batch_start}: {exc}"
            ) from exc

        records: List[Dict[str, object]] = []
        for image_id in image_ids:
            image_url = image_url_map.get(image_id)
            if image_url is None:
                raise Exception(
                    f"Image upload failed for batch starting at {batch_start}: missing URL for {image_id}"
                )
            records.append(
                {
                    "image_url": image_url,
                    "image_inline": False,
                    "image_storage": "minio",
                }
            )

        return image_ids, records
