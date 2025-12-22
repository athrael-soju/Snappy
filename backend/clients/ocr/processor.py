"""OCR processing logic - extracted from qdrant/indexing/ocr.py."""

from __future__ import annotations

import base64
import io
import logging
import re
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Sequence

from PIL import Image
from utils.timing import log_execution_time

if TYPE_CHECKING:  # pragma: no cover - hints only
    from clients.local_storage import LocalStorageClient
    from domain.ocr_persistence import OcrStorageHandler
    from domain.pipeline.image_processor import ImageProcessor

    from .client import OcrClient

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
        ocr_service: "OcrClient",
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
        include_grounding: Optional[bool] = None,
        include_images: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        Process a single image through DeepSeek OCR.

        Args:
            image_bytes: Raw image bytes
            filename: Filename for OCR service
            mode: OCR processing mode (Gundam, Tiny, etc.)
            task: OCR task type (markdown, plain_ocr, etc.)
            custom_prompt: Custom prompt for custom tasks
            include_grounding: Whether to extract bounding boxes
            include_images: Whether to extract embedded images

        Returns:
            Structured OCR result with text, regions, and extracted images
        """
        # Determine effective mode and task
        effective_mode = mode or self._ocr_service.default_mode
        effective_task = task or self._ocr_service.default_task

        logger.debug(
            f"Processing OCR for {filename} with mode={effective_mode}, task={effective_task}"
        )

        # Call DeepSeek OCR
        response = self._ocr_service.run_ocr_bytes(
            image_bytes,
            filename=filename,
            mode=mode,
            task=task,
            custom_prompt=custom_prompt,
            include_grounding=include_grounding,
            include_images=include_images,
        )

        # Validate response
        if not isinstance(response, dict):
            raise ValueError(f"Invalid OCR response type: {type(response)}")

        # Extract text fields based on task type
        # For markdown task, prioritize markdown output; for others, use plain text
        task_type = task or self._ocr_service.default_task

        if task_type == "markdown":
            # For markdown task, use markdown as primary and text as fallback
            markdown = (response.get("markdown") or "").strip()
            text = markdown  # Use markdown content for text field too
        else:
            # For other tasks (plain_ocr, locate, describe, custom), use text field
            text = (response.get("text") or "").strip()
            markdown = (response.get("markdown") or text).strip()

        raw_text = (response.get("raw") or text).strip()
        text_segments = self._split_segments(text)

        # Convert bounding boxes to regions with content
        bounding_boxes = response.get("bounding_boxes") or []
        regions = self._build_regions_from_bboxes(filename, bounding_boxes, raw_text)

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

    @log_execution_time("OCR batch", log_level=logging.DEBUG, warn_threshold_ms=15000)
    def process_batch(
        self,
        filename: str,
        page_numbers: List[int],
        storage_service: "LocalStorageClient",
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
            storage_service: Storage service for fetching images
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
                    storage_service,
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
        document_id: str,
        filename: str,
        page_number: int,
        storage_service: "LocalStorageClient",
        storage_handler: "OcrStorageHandler",
        mode: Optional[str],
        task: Optional[str],
    ) -> Dict[str, Any]:
        """Process a single page and store results."""
        # Fetch image
        image_bytes = self._fetch_page_image(storage_service, document_id, page_number)

        # Process with OCR
        ocr_result = self.process_single(
            image_bytes=image_bytes,
            filename=f"{filename}/page_{page_number}.png",
            mode=mode,
            task=task,
        )

        # Prepare metadata
        metadata = {"filename": filename}

        # store_ocr_result modifies ocr_result in-place with image URLs
        storage_handler.store_ocr_result(
            ocr_result=ocr_result,
            document_id=document_id,
            page_number=page_number,
            metadata=metadata,
        )

        return {
            "status": "success",
            "filename": filename,
            "page_number": page_number,
            "text_preview": ocr_result.get("text", "")[:200],
            "regions": len(ocr_result.get("regions", [])),
            "extracted_images": len(ocr_result.get("crops", [])),
        }

    def _fetch_page_image(
        self, storage_service: "LocalStorageClient", document_id: str, page_number: int
    ) -> bytes:
        """Fetch page image bytes from storage.

        Note: With UUID-based naming, we need to list objects in the image/ subfolder
        to find the page image since we don't have the image UUID readily available.
        """
        # List objects in the image/ subfolder for this page
        prefix = f"{document_id}/{page_number}/image/"

        for obj in storage_service.service.list_objects(
            bucket_name=storage_service.bucket_name,
            prefix=prefix,
        ):
            object_name = getattr(obj, "object_name", "")
            if object_name:
                # Found the page image, fetch it
                response = storage_service.service.get_object(
                    bucket_name=storage_service.bucket_name,
                    object_name=object_name,
                )
                return response.read()

        # No image found
        raise FileNotFoundError(
            f"Page image not found for document {document_id} page {page_number} in image/ subfolder"
        )

    def _split_segments(self, text: str) -> List[str]:
        """Split OCR text into distinct segments."""
        segments: List[str] = []
        for chunk in (text or "").splitlines():
            cleaned = chunk.strip()
            if cleaned:
                segments.append(cleaned)
        return segments

    def _build_regions_from_bboxes(
        self, doc_id: str, bboxes: Sequence[Dict[str, Any]], raw_text: str = ""
    ) -> List[Dict[str, Any]]:
        """
        Convert bounding boxes to region descriptors with content extraction.

        Args:
            doc_id: Document identifier for region IDs
            bboxes: List of bounding box dictionaries with label and coordinates
            raw_text: Raw OCR output with grounding references for content extraction

        Returns:
            List of region dictionaries with id, label, bbox, and content
        """
        regions: List[Dict[str, Any]] = []

        # Extract content mapping from raw text if available
        content_map = self._extract_region_content(raw_text) if raw_text else {}

        # Track image index for mapping crops to regions
        image_idx = 0

        for idx, bbox in enumerate(bboxes or [], start=1):
            try:
                x1 = int(bbox.get("x1", 0))
                y1 = int(bbox.get("y1", 0))
                x2 = int(bbox.get("x2", 0))
                y2 = int(bbox.get("y2", 0))
                label = bbox.get("label", "unknown")

                region = {
                    "id": f"{doc_id}#region-{idx}",
                    "label": label,
                    "bbox": [x1, y1, x2, y2],
                }

                # Add content if available
                if label in content_map and content_map[label]:
                    # For multiple instances of the same label, use them in order
                    content_list = content_map[label]
                    if content_list:
                        region["content"] = content_list.pop(0)

                # Track image index for mapping to extracted crops
                # Crops are extracted in order of image labels, so we need to map them
                if label.lower() in ("image", "figure"):
                    region["image_index"] = image_idx
                    image_idx += 1

                regions.append(region)
            except Exception:  # pragma: no cover - best effort
                continue
        return regions

    @staticmethod
    def _extract_region_content(raw_text: str) -> Dict[str, List[str]]:
        """
        Extract content for each labeled region from raw OCR output.

        The raw text contains patterns like:
        <|ref|>label<|/ref|><|det|>[[coords]]<|/det|>
        Content here

        Args:
            raw_text: Raw OCR output with grounding references

        Returns:
            Dictionary mapping labels to lists of their content
        """
        import re

        content_map: Dict[str, List[str]] = {}

        if not raw_text:
            return content_map

        # Pattern to match: <|ref|>label<|/ref|><|det|>coords<|/det|>Content
        # This captures the label and the content following it
        pattern = (
            r"<\|ref\|>([^<]+)<\|/ref\|><\|det\|>.*?<\|/det\|>\s*(.*?)(?=<\|ref\|>|$)"
        )

        matches = re.findall(pattern, raw_text, re.DOTALL)

        for label, content in matches:
            label = label.strip()
            content = content.strip()

            if label not in content_map:
                content_map[label] = []

            # Clean the content - remove any remaining grounding markers
            content = re.sub(r"<\|[^|]+\|>", "", content)
            content = content.strip()

            if content:
                content_map[label].append(content)

        return content_map

    def process_extracted_images(
        self,
        crops: List[str],
        document_id: str,
        page_number: int,
        storage_service: "LocalStorageClient",
    ) -> List[str]:
        """
        Process base64-encoded extracted images and upload to storage.

        Args:
            crops: List of base64-encoded image strings from DeepSeek OCR
            document_id: Document UUID for storage hierarchy
            page_number: Page number for storage hierarchy
            storage_service: Storage service for uploads

        Returns:
            List of storage URLs for uploaded images
        """
        if not crops:
            return []

        image_urls = []

        for crop_b64 in crops:
            try:
                # Decode base64 to PIL Image
                image_data = base64.b64decode(crop_b64)
                pil_image = Image.open(io.BytesIO(image_data))

                # Process image
                processed = self._image_processor.process(pil_image)

                # Storage structure: {doc_uuid}/{page_number}/ocr_regions/{uuid}.{ext}
                ext = self._image_processor.get_extension()
                region_uuid = str(uuid.uuid4())
                object_name = (
                    f"{document_id}/{page_number}/ocr_regions/{region_uuid}.{ext}"
                )

                # Upload to storage
                buf = processed.to_buffer()
                storage_service.service.put_object(
                    bucket_name=storage_service.bucket_name,
                    object_name=object_name,
                    data=buf,
                    length=processed.size,
                    content_type=processed.content_type,
                )

                # Generate public URL
                url = storage_service._get_image_url(object_name)
                image_urls.append(url)

                logger.debug(
                    f"Uploaded extracted image to {object_name} "
                    f"(format={processed.format}, size={processed.size} bytes)"
                )

            except Exception as exc:
                logger.warning(
                    f"Failed to process extracted image: {exc}", exc_info=True
                )
                continue

        return image_urls

    @staticmethod
    def replace_base64_with_urls(markdown: str, image_urls: List[str]) -> str:
        """
        Replace base64-encoded image data URLs in markdown with storage URLs.

        Args:
            markdown: Markdown text with base64 image data URLs
            image_urls: List of storage URLs to replace with

        Returns:
            Updated markdown with storage URLs
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
