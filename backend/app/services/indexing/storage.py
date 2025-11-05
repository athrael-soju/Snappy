"""Image storage helpers for document indexing workflows."""

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
        meta_batch: List[dict],
    ) -> Tuple[List[str], List[Dict[str, object]]]:
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
        Tuple[List[str], List[Dict[str, object]]]
            image_ids and image_records
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

        try:
            image_url_map = self._minio_service.store_images_batch(
                image_batch,
                image_ids=image_ids,
                filenames=filenames,
                page_numbers=page_numbers,
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
