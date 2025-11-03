"""DeepSeek OCR integration helpers for the indexing pipeline."""

from __future__ import annotations

import io
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Sequence

import config

if TYPE_CHECKING:  # pragma: no cover - hints only
    from PIL import Image
    from services.deepseek import DeepSeekOCRService
    from services.minio import MinioService

from .progress import ProgressNotifier

logger = logging.getLogger(__name__)


class OcrResultHandler:
    """Runs DeepSeek OCR on indexed pages and persists structured results."""

    def __init__(
        self,
        ocr_service: "DeepSeekOCRService",
        minio_service: "MinioService",
    ):
        if not ocr_service or not ocr_service.is_enabled():
            raise ValueError("DeepSeek OCR service must be enabled to instantiate.")

        self._ocr_service = ocr_service
        self._minio = minio_service

        # Get max workers from config
        max_workers_config = getattr(config, "DEEPSEEK_OCR_MAX_WORKERS", None)
        if max_workers_config:
            self._max_workers = max(1, min(16, int(max_workers_config)))
        else:
            # Fallback: use pipeline concurrency setting
            max_workers = config.get_pipeline_max_concurrency()
            self._max_workers = max(1, min(int(max_workers) or 1, 4))

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def process_batch(
        self,
        *,
        batch_start: int,
        total_images: int,
        image_ids: List[str],
        image_batch: List["Image.Image"],
        meta_batch: List[dict],
        image_records: List[Dict[str, object]],
        progress: ProgressNotifier,
        skip_progress: bool = False,
    ) -> List[Optional[Dict[str, Any]]]:
        """Run OCR over a batch of images and return per-page summaries."""
        if not image_ids:
            return []

        progress.check_cancel(batch_start)

        encoded_images = [self._encode_image(image) for image in image_batch]
        results: List[Optional[Dict[str, Any]]] = [None] * len(image_ids)

        max_workers = max(1, min(self._max_workers, len(encoded_images)))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(
                    self._process_single,
                    image_ids[idx],
                    encoded_images[idx],
                    meta_batch[idx] if idx < len(meta_batch) else {},
                    image_records[idx] if idx < len(image_records) else {},
                ): idx
                for idx in range(len(image_ids))
            }

            for future in as_completed(futures):
                offset = futures[future]
                current_index = batch_start + offset + 1
                progress.check_cancel(current_index - 1)
                try:
                    result = future.result()
                except Exception as exc:  # pragma: no cover - defensive guard
                    doc_id = image_ids[offset]
                    logger.exception(
                        "DeepSeek OCR processing failed for %s: %s", doc_id, exc
                    )
                    result = {
                        "status": "error",
                        "error": str(exc),
                    }

                results[offset] = result

                # Unified progress: "Processing page X/Y" (includes OCR)
                if not skip_progress:
                    progress.stage(
                        current=min(current_index, total_images),
                        stage="processing",
                        batch_start=current_index - 1,
                        batch_size=1,
                        total=total_images,
                    )

        return results

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _encode_image(self, image: "Image.Image") -> bytes:
        """Serialize a PIL image into PNG bytes."""
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return buffer.getvalue()

    def _process_single(
        self,
        doc_id: str,
        image_bytes: bytes,
        meta: Dict[str, Any],
        image_record: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Process one page through DeepSeek OCR and persist the results."""
        filename = meta.get("filename") or f"{doc_id}.png"
        response = self._ocr_service.run_ocr_bytes(
            image_bytes,
            filename=filename,
        )

        # Validate response format
        if not isinstance(response, dict):
            raise ValueError(f"Invalid OCR response type: {type(response)}")

        # Check for error status
        if not response.get("success"):
            error = response.get("error", "Unknown error")
            return {
                "status": "error",
                "error": f"OCR processing failed: {error}",
            }

        # Extract text fields
        text = (response.get("text") or "").strip()
        raw_text = (response.get("raw_text") or text).strip()
        text_segments = self._split_segments(text)
        regions = self._build_regions(doc_id, response.get("boxes") or [])

        # Extract image dimensions from response
        image_dims = response.get("image_dims") or {}
        original_width = image_dims.get("w")
        original_height = image_dims.get("h")

        payload = {
            "provider": "deepseek-ocr",
            "version": "1.0",
            "document_id": doc_id,
            "filename": filename,
            "pdf_page_index": meta.get("pdf_page_index"),
            "total_pages": meta.get("total_pages"),
            "page_dimensions": {
                "width_px": meta.get("page_width_px"),
                "height_px": meta.get("page_height_px"),
            },
            "image": {
                "url": image_record.get("image_url"),
                "storage": image_record.get("image_storage"),
            },
            "text": text,
            "raw_text": raw_text,
            "text_segments": text_segments,
            "regions": regions,
            "metadata": {
                "original_width": original_width,
                "original_height": original_height,
            },
            "extracted_at": datetime.now(timezone.utc).isoformat(),
        }

        # Require hierarchical structure metadata
        document_id = meta.get("document_id")
        page_number = meta.get("page_number")

        if document_id is None or page_number is None:
            raise ValueError(
                f"Metadata must contain 'document_id' and 'page_number' for OCR storage. Got: {meta}"
            )

        # Storage structure: {document_id}/{page_number}/ocr/elements.json
        url = self._minio.store_json(
            payload=payload,
            document_id=document_id,
            page_number=page_number,
            filename="elements.json",
        )

        preview = self._build_preview(text_segments, text)
        result = {
            "status": "success",
            "elements_url": url,
            "text_preview": preview,
            "text_segments": len(text_segments),
            "regions": len(regions),
        }
        return result

    def _split_segments(self, text: str) -> List[str]:
        """Split OCR text into distinct segments."""
        segments: List[str] = []
        for chunk in (text or "").splitlines():
            cleaned = chunk.strip()
            if cleaned:
                segments.append(cleaned)
        return segments

    def _build_regions(
        self, doc_id: str, boxes: Sequence[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Normalise detection boxes into region descriptors."""
        regions: List[Dict[str, Any]] = []
        for idx, box in enumerate(boxes or [], start=1):
            coords = box.get("box") or box.get("bbox")
            if not isinstance(coords, (list, tuple)) or len(coords) < 4:
                continue
            try:
                normalized = [int(float(value)) for value in coords[:4]]
            except Exception:  # pragma: no cover - best effort
                continue

            regions.append(
                {
                    "id": f"{doc_id}#region-{idx}",
                    "label": box.get("label"),
                    "bbox": normalized,
                }
            )
        return regions

    def _build_preview(
        self, segments: Sequence[str], fallback_text: str, limit: int = 160
    ) -> Optional[str]:
        """Generate a concise preview string for UI surfaces."""
        if segments:
            preview = " ".join(segments[:2])
        else:
            preview = (fallback_text or "").strip()
        preview = preview.strip()
        if not preview:
            return None
        return preview[:limit]
