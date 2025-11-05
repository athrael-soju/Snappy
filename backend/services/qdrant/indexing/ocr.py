"""DeepSeek OCR integration helpers for the indexing pipeline."""

from __future__ import annotations

import base64
import io
import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Sequence

import config
from PIL import Image

if TYPE_CHECKING:  # pragma: no cover - hints only
    from services.deepseek import DeepSeekOCRService
    from services.image_processor import ProcessedImage
    from services.minio import MinioService

from .progress import ProgressNotifier

logger = logging.getLogger(__name__)


class OcrResultHandler:
    """Runs DeepSeek OCR on indexed pages and persists structured results."""

    def __init__(
        self,
        ocr_service: "DeepSeekOCRService",
        minio_service: "MinioService",
        image_processor=None,
    ):
        if not ocr_service or not ocr_service.is_enabled():
            raise ValueError("DeepSeek OCR service must be enabled to instantiate.")

        self._ocr_service = ocr_service
        self._minio = minio_service

        # Import here to avoid circular dependency
        if image_processor is None:
            from services.image_processor import ImageProcessor

            image_processor = ImageProcessor(
                default_format=config.IMAGE_FORMAT,
                default_quality=config.IMAGE_QUALITY,
            )
        self._image_processor = image_processor

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
        processed_images: List["ProcessedImage"],
        meta_batch: List[dict],
        image_records: List[Dict[str, object]],
        progress: ProgressNotifier,
        skip_progress: bool = False,
    ) -> List[Optional[Dict[str, Any]]]:
        """
        Run OCR over a batch of pre-processed images and return per-page summaries.

        Parameters
        ----------
        batch_start : int
            Starting index of this batch
        total_images : int
            Total number of images in the entire indexing job
        image_ids : List[str]
            IDs for each image in the batch
        processed_images : List[ProcessedImage]
            Pre-processed images with encoded data (no redundant conversion needed)
        meta_batch : List[dict]
            Metadata for each image
        image_records : List[Dict[str, object]]
            Image storage records (URLs, etc.)
        progress : ProgressNotifier
            Progress tracking callback
        skip_progress : bool
            Whether to skip progress updates

        Returns
        -------
        List[Optional[Dict[str, Any]]]
            OCR results for each image
        """
        if not image_ids:
            return []

        progress.check_cancel(batch_start)

        # Use pre-processed image bytes directly (no conversion needed!)
        results: List[Optional[Dict[str, Any]]] = [None] * len(image_ids)

        max_workers = max(1, min(self._max_workers, len(processed_images)))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(
                    self._process_single,
                    image_ids[idx],
                    processed_images[idx].data,  # Use pre-processed bytes
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

    def _process_single(
        self,
        doc_id: str,
        image_bytes: bytes,
        meta: Dict[str, Any],
        image_record: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Process one page through DeepSeek OCR and persist the results."""
        filename = meta.get("filename") or f"{doc_id}.png"

        # Call DeepSeek OCR with service's default settings
        # (uses DEEPSEEK_OCR_TASK, DEEPSEEK_OCR_MODE, DEEPSEEK_OCR_INCLUDE_GROUNDING,
        #  DEEPSEEK_OCR_INCLUDE_IMAGES from config)
        response = self._ocr_service.run_ocr_bytes(
            image_bytes,
            filename=filename,
            # Don't override defaults - use config values
        )

        # Validate response format
        if not isinstance(response, dict):
            raise ValueError(f"Invalid OCR response type: {type(response)}")

        # Extract text fields from new response structure
        text = (response.get("text") or "").strip()
        markdown = (response.get("markdown") or text).strip()
        raw_text = (response.get("raw") or text).strip()
        text_segments = self._split_segments(text)

        # Convert bounding boxes to regions format
        bounding_boxes = response.get("bounding_boxes") or []
        regions = self._build_regions_from_bboxes(doc_id, bounding_boxes)

        # Process extracted images (if any) and upload to MinIO
        extracted_images_urls = []
        crops = response.get("crops") or []
        doc_filename = meta.get("filename")
        page_number = meta.get("page_number")

        if crops and doc_filename and page_number is not None:
            try:
                extracted_images_urls = self._process_extracted_images(
                    crops=crops,
                    filename=doc_filename,
                    page_number=page_number,
                )
                # Replace base64 image URLs in markdown with MinIO URLs
                markdown = self._replace_base64_with_urls(
                    markdown, extracted_images_urls
                )
            except Exception as exc:
                logger.warning(
                    f"Failed to process extracted images for {doc_id}: {exc}",
                    exc_info=True,
                )

        # Build payload for storage
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
            "markdown": markdown,
            "raw_text": raw_text,
            "text_segments": text_segments,
            "regions": regions,
            "extracted_at": datetime.now(timezone.utc).isoformat(),
        }

        # Add extracted images metadata if any
        if extracted_images_urls:
            payload["extracted_images"] = [
                {"url": url, "storage": "minio"} for url in extracted_images_urls
            ]

        # Validate hierarchical structure metadata (already extracted above)
        if doc_filename is None or page_number is None:
            raise ValueError(
                f"Metadata must contain 'filename' and 'page_number' for OCR storage. Got: {meta}"
            )

        # Storage structure: {filename}/{page_number}/elements.json
        url = self._minio.store_json(
            payload=payload,
            filename=doc_filename,
            page_number=page_number,
            json_filename="elements.json",
        )

        preview = self._build_preview(text_segments, text)
        result = {
            "status": "success",
            "elements_url": url,
            "text_preview": preview,
            "text_segments": len(text_segments),
            "regions": len(regions),
            "extracted_images": len(extracted_images_urls),
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

    def _build_regions_from_bboxes(
        self, doc_id: str, bboxes: Sequence[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Convert bounding boxes to region descriptors."""
        regions: List[Dict[str, Any]] = []
        for idx, bbox in enumerate(bboxes or [], start=1):
            # New format has x1, y1, x2, y2, label
            try:
                x1 = int(bbox.get("x1", 0))
                y1 = int(bbox.get("y1", 0))
                x2 = int(bbox.get("x2", 0))
                y2 = int(bbox.get("y2", 0))
                label = bbox.get("label", "unknown")

                regions.append(
                    {
                        "id": f"{doc_id}#region-{idx}",
                        "label": label,
                        "bbox": [x1, y1, x2, y2],
                    }
                )
            except Exception:  # pragma: no cover - best effort
                continue
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

    def _process_extracted_images(
        self,
        crops: List[str],
        filename: str,
        page_number: int,
    ) -> List[str]:
        """
        Process base64-encoded extracted images and upload to MinIO.

        Args:
            crops: List of base64-encoded image strings from DeepSeek OCR
            filename: Document filename for storage hierarchy
            page_number: Page number for storage hierarchy

        Returns:
            List of MinIO URLs for uploaded images
        """
        if not crops:
            return []

        image_urls = []

        for idx, crop_b64 in enumerate(crops, start=1):
            try:
                # Decode base64 to PIL Image
                image_data = base64.b64decode(crop_b64)
                pil_image = Image.open(io.BytesIO(image_data))

                # Process image using centralized processor (respects IMAGE_FORMAT/IMAGE_QUALITY)
                processed = self._image_processor.process(pil_image)

                # Storage structure: {filename}/{page_number}/figure_{idx}.{ext}
                ext = self._image_processor.get_extension()
                object_name = f"{filename}/{page_number}/figure_{idx}.{ext}"

                # Upload to MinIO
                buf = processed.to_buffer()
                self._minio.service.put_object(
                    bucket_name=self._minio.bucket_name,
                    object_name=object_name,
                    data=buf,
                    length=processed.size,
                    content_type=processed.content_type,
                )

                # Generate public URL
                url = self._minio._get_image_url(object_name)
                image_urls.append(url)

                logger.debug(
                    f"Uploaded extracted image {idx} to {object_name} "
                    f"(format={processed.format}, size={processed.size} bytes)"
                )

            except Exception as exc:
                logger.warning(
                    f"Failed to process extracted image {idx}: {exc}",
                    exc_info=True,
                )
                continue

        return image_urls

    def _replace_base64_with_urls(self, markdown: str, image_urls: List[str]) -> str:
        """
        Replace base64-encoded image data URLs in markdown with MinIO URLs.

        Args:
            markdown: Markdown text with base64 image data URLs
            image_urls: List of MinIO URLs to replace with

        Returns:
            Updated markdown with MinIO URLs
        """
        if not image_urls:
            return markdown

        # Pattern to match base64 image data URLs in markdown
        # Format: ![Figure N](data:image/png;base64,...)
        pattern = r"!\[Figure (\d+)\]\(data:image/[^;]+;base64,[^)]+\)"

        def replacer(match):
            figure_num = int(match.group(1))
            # Figure numbers are 1-indexed
            if 1 <= figure_num <= len(image_urls):
                url = image_urls[figure_num - 1]
                return f"![Figure {figure_num}]({url})"
            return match.group(0)  # Keep original if no URL available

        return re.sub(pattern, replacer, markdown)
