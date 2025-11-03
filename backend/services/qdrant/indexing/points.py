"""Point construction helpers for Qdrant indexing."""

import logging
from datetime import datetime
from typing import Dict, List

import config
from qdrant_client import models

logger = logging.getLogger(__name__)


class PointFactory:
    """Builds Qdrant point payloads and vector data."""

    def __init__(self, muvera_post=None):
        self._muvera_post = muvera_post

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
    ) -> List[models.PointStruct]:
        points: List[models.PointStruct] = []
        use_mean_pooling = bool(config.QDRANT_MEAN_POOLING_ENABLED)

        for offset, (orig, doc_id, image_info, meta) in enumerate(
            zip(original_batch, image_ids, image_records, meta_batch)
        ):
            rows = None
            cols = None
            if use_mean_pooling and pooled_by_rows_batch and pooled_by_columns_batch:
                rows = pooled_by_rows_batch[offset]
                cols = pooled_by_columns_batch[offset]

            now_iso = datetime.now().isoformat() + "Z"
            image_url = None
            image_inline = False
            image_storage = None
            image_mime = None
            image_format = None
            image_size_bytes = None
            image_quality = None

            if isinstance(image_info, dict):
                image_url = image_info.get("image_url")
                image_inline = bool(image_info.get("image_inline"))
                image_storage = image_info.get("image_storage")
                image_mime = image_info.get("image_mime_type")
                image_format = image_info.get("image_format")
                image_size_bytes = image_info.get("image_size_bytes")
                image_quality = image_info.get("image_quality")

            payload = {
                "index": batch_start + offset,
                "image_url": image_url,
                "image_inline": image_inline,
                "image_storage": image_storage,
                "document_id": doc_id,
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
            if image_quality is not None:
                payload["image_quality"] = image_quality

            ocr_summary = meta.get("ocr") if isinstance(meta, dict) else None
            if isinstance(ocr_summary, dict) and ocr_summary.get("elements_url"):
                ocr_payload = {
                    "elements_url": ocr_summary.get("elements_url"),
                    "text_preview": ocr_summary.get("text_preview"),
                    "text_segments": ocr_summary.get("text_segments"),
                    "regions": ocr_summary.get("regions"),
                    "status": ocr_summary.get("status", "success"),
                }
                if "error" in ocr_summary:
                    ocr_payload["error"] = ocr_summary["error"]
                payload["ocr"] = ocr_payload

            vectors = {"original": orig}
            if use_mean_pooling and rows is not None and cols is not None:
                vectors["mean_pooling_columns"] = cols
                vectors["mean_pooling_rows"] = rows

            if self._muvera_post and self._muvera_post.enabled:
                try:
                    fde = self._muvera_post.process_document(orig)
                    if fde is not None:
                        vectors["muvera_fde"] = fde
                    else:
                        logger.debug("No MUVERA FDE produced for doc_id=%s", doc_id)
                except Exception as exc:
                    logger.warning(
                        "Failed to compute MUVERA FDE for doc %s: %s", doc_id, exc
                    )

            points.append(
                models.PointStruct(
                    id=doc_id,
                    vector=vectors,
                    payload=payload,
                )
            )

        return points
