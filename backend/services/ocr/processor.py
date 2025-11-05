"""OCR processing logic - extracted from qdrant/indexing/ocr.py."""

from __future__ import annotations

import base64
import io
import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Sequence

from PIL import Image

if TYPE_CHECKING:  # pragma: no cover - hints only
    from services.image_processor import ImageProcessor
    from services.minio import MinioService

    from .service import OcrService
    from .storage import OcrStorageHandler

logger = logging.getLogger(__name__)


class OcrProcessor:
    """
    Processes images with DeepSeek OCR and formats results.

    Responsibilities:
    - Execute OCR on image bytes
    - Parse and structure OCR responses
    - Extract and process embedded images
    - Format results for storage
    """

    def __init__(
        self,
        ocr_service: "OcrService",
        image_processor: "ImageProcessor",
    ):
        """
        Initialize OCR processor.

        Args:
            ocr_service: OCR service (main orchestrator)
            image_processor: Image processing service
        """
        if not ocr_service or not ocr_service.is_enabled():
            raise ValueError("DeepSeek OCR service must be enabled")

        self._ocr_service = ocr_service
        self._image_processor = image_processor

    def process_single(
        self,
        image_bytes: bytes,
        filename: str,
        *,
        mode: Optional[str] = None,
        task: Optional[str] = None,
        custom_prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Process a single image through DeepSeek OCR.

        Args:
            image_bytes: Raw image bytes
            filename: Filename for OCR service
            mode: OCR processing mode (Gundam, Tiny, etc.)
            task: OCR task type (markdown, plain_ocr, etc.)
            custom_prompt: Custom prompt for custom tasks

        Returns:
            Structured OCR result with text, regions, and extracted images
        """
        # Call DeepSeek OCR
        response = self._ocr_service.run_ocr_bytes(
            image_bytes,
            filename=filename,
            mode=mode,
            task=task,
            custom_prompt=custom_prompt,
        )

        # Validate response
        if not isinstance(response, dict):
            raise ValueError(f"Invalid OCR response type: {type(response)}")

        # Extract text fields
        text = (response.get("text") or "").strip()
        markdown = (response.get("markdown") or text).strip()
        raw_text = (response.get("raw") or text).strip()
        text_segments = self._split_segments(text)

        # Convert bounding boxes to regions
        bounding_boxes = response.get("bounding_boxes") or []
        regions = self._build_regions_from_bboxes(filename, bounding_boxes)

        # Extract base64-encoded images if present
        crops = response.get("crops") or []

        return {
            "text": text,
            "markdown": markdown,
            "raw_text": raw_text,
            "text_segments": text_segments,
            "regions": regions,
            "crops": crops,  # Pass through for storage handler to process
        }

    def process_batch(
        self,
        filename: str,
        page_numbers: List[int],
        minio_service: "MinioService",
        storage_handler: "OcrStorageHandler",
        *,
        mode: Optional[str] = None,
        task: Optional[str] = None,
        max_workers: Optional[int] = None,
    ) -> List[Optional[Dict[str, Any]]]:
        """
        Process multiple pages in parallel.

        Args:
            filename: Document filename
            page_numbers: List of page numbers to process
            minio_service: MinIO service for fetching images
            storage_handler: OCR storage handler
            mode: OCR processing mode
            task: OCR task type
            max_workers: Concurrent processing workers

        Returns:
            List of OCR result summaries
        """
        if not page_numbers:
            return []

        # Determine worker count
        if max_workers is None:
            import config

            max_workers_config = getattr(config, "DEEPSEEK_OCR_MAX_WORKERS", None)
            if max_workers_config:
                max_workers = max(1, min(16, int(max_workers_config)))
            else:
                max_workers = 4

        max_workers = max(1, min(max_workers, len(page_numbers)))

        results: List[Optional[Dict[str, Any]]] = [None] * len(page_numbers)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(
                    self._process_page_with_storage,
                    filename,
                    page_num,
                    minio_service,
                    storage_handler,
                    mode,
                    task,
                ): idx
                for idx, page_num in enumerate(page_numbers)
            }

            for future in as_completed(futures):
                idx = futures[future]
                try:
                    result = future.result()
                    results[idx] = result
                except Exception as exc:
                    logger.exception(
                        f"OCR processing failed for {filename} page {page_numbers[idx]}: {exc}"
                    )
                    results[idx] = {
                        "status": "error",
                        "filename": filename,
                        "page_number": page_numbers[idx],
                        "error": str(exc),
                    }

        return results

    def _process_page_with_storage(
        self,
        filename: str,
        page_number: int,
        minio_service: "MinioService",
        storage_handler: "OcrStorageHandler",
        mode: Optional[str],
        task: Optional[str],
    ) -> Dict[str, Any]:
        """Process a single page and store results."""
        # Fetch image
        image_bytes = self._fetch_page_image(minio_service, filename, page_number)

        # Process with OCR
        ocr_result = self.process_single(
            image_bytes=image_bytes,
            filename=f"{filename}/page_{page_number}.png",
            mode=mode,
            task=task,
        )

        # Store results
        storage_url = storage_handler.store_ocr_result(
            ocr_result=ocr_result,
            filename=filename,
            page_number=page_number,
        )

        return {
            "status": "success",
            "filename": filename,
            "page_number": page_number,
            "storage_url": storage_url,
            "text_preview": ocr_result.get("text", "")[:200],
            "regions": len(ocr_result.get("regions", [])),
            "extracted_images": len(ocr_result.get("crops", [])),
        }

    def _fetch_page_image(
        self, minio_service: "MinioService", filename: str, page_number: int
    ) -> bytes:
        """Fetch page image bytes from MinIO."""
        ext = self._image_processor.get_extension()
        object_name = f"{filename}/{page_number}/page.{ext}"

        response = minio_service.service.get_object(
            bucket_name=minio_service.bucket_name,
            object_name=object_name,
        )

        return response.read()

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

    def process_extracted_images(
        self,
        crops: List[str],
        filename: str,
        page_number: int,
        minio_service: "MinioService",
    ) -> List[str]:
        """
        Process base64-encoded extracted images and upload to MinIO.

        Args:
            crops: List of base64-encoded image strings from DeepSeek OCR
            filename: Document filename for storage hierarchy
            page_number: Page number for storage hierarchy
            minio_service: MinIO service for uploads

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

                # Process image
                processed = self._image_processor.process(pil_image)

                # Storage structure: {filename}/{page_number}/figure_{idx}.{ext}
                ext = self._image_processor.get_extension()
                object_name = f"{filename}/{page_number}/figure_{idx}.{ext}"

                # Upload to MinIO
                buf = processed.to_buffer()
                minio_service.service.put_object(
                    bucket_name=minio_service.bucket_name,
                    object_name=object_name,
                    data=buf,
                    length=processed.size,
                    content_type=processed.content_type,
                )

                # Generate public URL
                url = minio_service._get_image_url(object_name)
                image_urls.append(url)

                logger.debug(
                    f"Uploaded extracted image {idx} to {object_name} "
                    f"(format={processed.format}, size={processed.size} bytes)"
                )

            except Exception as exc:
                logger.warning(
                    f"Failed to process extracted image {idx}: {exc}", exc_info=True
                )
                continue

        return image_urls

    @staticmethod
    def replace_base64_with_urls(markdown: str, image_urls: List[str]) -> str:
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
