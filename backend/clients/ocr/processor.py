"""OCR processing logic - simplified for inline storage."""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Sequence

if TYPE_CHECKING:  # pragma: no cover - hints only
    from domain.pipeline.image_processor import ImageProcessor

    from .client import OcrClient

logger = logging.getLogger(__name__)


class OcrProcessor:
    """
    Processes images with DeepSeek OCR and formats results.

    Responsibilities:
    - Execute OCR on image bytes
    - Parse and structure OCR responses
    - Format results for inline storage in Qdrant
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

        return {
            "text": text,
            "markdown": markdown,
            "raw_text": raw_text,
            "text_segments": text_segments,
            "regions": regions,
        }

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

    def _extract_region_content(self, raw_text: str) -> Dict[str, List[str]]:
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
