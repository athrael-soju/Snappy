"""Point construction helpers for Qdrant indexing."""

import logging
from datetime import datetime
from typing import Any, Dict, List

import config
from qdrant_client import models

logger = logging.getLogger(__name__)


class PointFactory:
    """Builds Qdrant point payloads and vector data with inline storage."""

    def __init__(self):
        pass

    def build(
        self,
        *,
        batch_start: int,
        original_batch,
        pooled_by_rows_batch,
        pooled_by_columns_batch,
        image_ids: List[str],
        image_records: List[Dict[str, Any]],
        meta_batch: List[dict],
        ocr_results: List[Dict] | None = None,
    ) -> List[models.PointStruct]:
        points: List[models.PointStruct] = []
        use_mean_pooling = bool(config.QDRANT_MEAN_POOLING_ENABLED)

        for offset, (orig, page_id, image_info, meta) in enumerate(
            zip(original_batch, image_ids, image_records, meta_batch)
        ):
            rows = None
            cols = None
            if use_mean_pooling and pooled_by_rows_batch and pooled_by_columns_batch:
                rows = pooled_by_rows_batch[offset]
                cols = pooled_by_columns_batch[offset]

            now_iso = datetime.now().isoformat() + "Z"

            # Extract inline image data
            image_data = None
            image_mime = None
            image_format = None
            image_size_bytes = None

            if isinstance(image_info, dict):
                # Image data is now base64 encoded
                image_data = image_info.get("image_data")
                image_mime = image_info.get("image_mime_type")
                image_format = image_info.get("image_format")
                image_size_bytes = image_info.get("image_size_bytes")

            # Get document_id from metadata (same for all pages in document)
            document_id = meta.get("document_id")

            payload = {
                "index": batch_start + offset,
                "page_id": page_id,
                "image_data": image_data,
                "document_id": document_id,
                "filename": meta.get("filename"),
                "file_size_bytes": meta.get("file_size_bytes"),
                "pdf_page_index": meta.get("pdf_page_index"),
                "total_pages": meta.get("total_pages"),
                "indexed_at": now_iso,
            }
            if image_mime:
                payload["image_mime_type"] = image_mime
            if image_format:
                payload["image_format"] = image_format
            if image_size_bytes is not None:
                payload["image_size_bytes"] = image_size_bytes

            # Add OCR data inline if available (from parallel OCR processing)
            if ocr_results and offset < len(ocr_results):
                ocr_result = ocr_results[offset]
                if ocr_result and isinstance(ocr_result, dict):
                    ocr_data = ocr_result.get("ocr_data")
                    if ocr_data:
                        payload["ocr_data"] = ocr_data

            vectors = {"original": orig}
            if use_mean_pooling and rows is not None and cols is not None:
                vectors["mean_pooling_columns"] = cols
                vectors["mean_pooling_rows"] = rows

            points.append(
                models.PointStruct(
                    id=page_id,  # Use page_id as point ID (unique per page)
                    vector=vectors,
                    payload=payload,
                )
            )

        return points
