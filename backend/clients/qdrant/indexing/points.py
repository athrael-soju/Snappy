"""Point construction helpers for Qdrant indexing."""

import logging
from datetime import datetime
from typing import Dict, List, Optional

import config
from qdrant_client import models

logger = logging.getLogger(__name__)


class PointFactory:
    """Builds Qdrant point payloads and vector data."""

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
        image_records: List[Dict[str, object]],
        meta_batch: List[dict],
        ocr_results: Optional[List[Dict]] = None,
    ) -> List[models.PointStruct]:
        """Build Qdrant points with embeddings and payload data.

        Supports both inline image storage (base64 in payload) and URL-based storage.
        """
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

            # Extract image info from record
            image_inline = False
            image_storage = None
            image_mime = None
            image_format = None
            image_size_bytes = None
            image_data = None
            image_data_full = None
            image_width = None
            image_height = None
            image_full_width = None
            image_full_height = None
            image_full_size_bytes = None

            if isinstance(image_info, dict):
                image_inline = bool(image_info.get("image_inline"))
                image_storage = image_info.get("image_storage")
                image_mime = image_info.get("image_mime_type")
                image_format = image_info.get("image_format")
                image_size_bytes = image_info.get("image_size_bytes")

                # Inline storage fields
                image_data = image_info.get("image_data")
                image_data_full = image_info.get("image_data_full")
                image_width = image_info.get("image_width")
                image_height = image_info.get("image_height")
                image_full_width = image_info.get("image_full_width")
                image_full_height = image_info.get("image_full_height")
                image_full_size_bytes = image_info.get("image_full_size_bytes")

            # Get document_id from metadata (same for all pages in document)
            document_id = meta.get("document_id")

            # Build base payload
            payload = {
                "index": batch_start + offset,
                "page_id": page_id,
                "image_inline": image_inline,
                "image_storage": image_storage,
                "document_id": document_id,
                "filename": meta.get("filename"),
                "file_size_bytes": meta.get("file_size_bytes"),
                "pdf_page_index": meta.get("pdf_page_index"),
                "total_pages": meta.get("total_pages"),
                "indexed_at": now_iso,
            }

            # Add image metadata
            if image_mime:
                payload["image_mime_type"] = image_mime
            if image_format:
                payload["image_format"] = image_format
            if image_size_bytes is not None:
                payload["image_size_bytes"] = image_size_bytes
            if image_width is not None:
                payload["image_width"] = image_width
            if image_height is not None:
                payload["image_height"] = image_height

            # Add inline image data (thumbnail for search results)
            if image_data:
                payload["image_data"] = image_data

            # Add full-resolution image data
            if image_data_full:
                payload["image_data_full"] = image_data_full
            if image_full_width is not None:
                payload["image_full_width"] = image_full_width
            if image_full_height is not None:
                payload["image_full_height"] = image_full_height
            if image_full_size_bytes is not None:
                payload["image_full_size_bytes"] = image_full_size_bytes

            # Add OCR metadata if available
            if ocr_results and offset < len(ocr_results):
                ocr_result = ocr_results[offset]
                if ocr_result and isinstance(ocr_result, dict):
                    # Inline OCR text (for Phase 2)
                    ocr_text = ocr_result.get("ocr_text")
                    ocr_markdown = ocr_result.get("ocr_markdown")
                    if ocr_text:
                        payload["ocr_text"] = ocr_text
                    if ocr_markdown:
                        payload["ocr_markdown"] = ocr_markdown

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
