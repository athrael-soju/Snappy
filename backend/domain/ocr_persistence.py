"""OCR result storage handling."""

from __future__ import annotations

import base64
import io
import logging
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from PIL import Image

if TYPE_CHECKING:  # pragma: no cover - hints only
    from clients.ocr.processor import OcrProcessor

logger = logging.getLogger(__name__)


class OcrStorageHandler:
    """
    Handles formatting of OCR results for inline storage in Qdrant.

    Responsibilities:
    - Format OCR results for Qdrant payloads
    - Convert extracted images to base64
    - Build structured OCR data
    """

    def __init__(
        self,
        processor: Optional["OcrProcessor"] = None,
    ):
        """
        Initialize storage handler.

        Args:
            processor: OCR processor (optional, for image extraction)
        """
        self._processor = processor

    def store_ocr_result(
        self,
        ocr_result: Dict[str, Any],
        document_id: str,
        page_number: int,
        *,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Format OCR result for inline storage in Qdrant payload.

        Args:
            ocr_result: Processed OCR result from OcrProcessor
            document_id: Document UUID
            page_number: Page number
            metadata: Optional additional metadata

        Returns:
            Dictionary with ocr_data structure:
            {
                "ocr_data": {
                    "text": "...",
                    "markdown": "...",
                    "raw_text": "...",
                    "regions": [...],
                    "extracted_images": ["base64_1", ...]
                }
            }
        """
        filename = metadata.get("filename") if metadata else None

        # Process extracted images to base64
        extracted_images_base64: List[str] = []
        crops = ocr_result.get("crops", [])
        regions = ocr_result.get("regions", [])

        if crops and self._processor:
            try:
                # Convert crop images to base64
                for crop in crops:
                    if isinstance(crop, Image.Image):
                        buffer = io.BytesIO()
                        # Use JPEG for smaller size
                        crop.save(buffer, format="JPEG", quality=85)
                        image_bytes = buffer.getvalue()
                        b64_str = base64.b64encode(image_bytes).decode("utf-8")
                        extracted_images_base64.append(b64_str)
                    else:
                        logger.warning(f"Skipping non-Image crop: {type(crop)}")
            except Exception as exc:
                logger.warning(
                    f"Failed to convert extracted images to base64 for document {document_id} page {page_number}: {exc}",
                    exc_info=True,
                )

        # Process regions and attach base64 image data
        processed_regions: List[Dict[str, Any]] = []
        if regions:
            for idx, region in enumerate(regions):
                # Generate unique ID for this region
                region_id = str(uuid.uuid4())

                # Attach extracted image data if available
                image_idx = region.pop("image_index", None)
                region_data: Dict[str, Any] = {
                    "id": region_id,
                    "label": region.get("label", "unknown"),
                    "bbox": region.get("bbox", []),
                    "content": region.get("content", ""),
                }

                if isinstance(image_idx, int) and 0 <= image_idx < len(
                    extracted_images_base64
                ):
                    region_data["image_data"] = extracted_images_base64[image_idx]

                processed_regions.append(region_data)

        # Build OCR data structure
        ocr_uuid = str(uuid.uuid4())
        ocr_data = {
            "id": ocr_uuid,
            "provider": "deepseek-ocr",
            "version": "1.0",
            "filename": filename,
            "page_number": page_number,
            "text": ocr_result.get("text", ""),
            "markdown": ocr_result.get("markdown", ""),
            "raw_text": ocr_result.get("raw_text", ""),
            "regions": processed_regions,
            "extracted_at": datetime.now(timezone.utc).isoformat(),
        }

        # Add metadata if provided
        if metadata:
            ocr_data.update(
                {
                    "document_id": metadata.get("document_id"),
                    "page_id": metadata.get("page_id"),
                    "pdf_page_index": metadata.get("pdf_page_index"),
                    "total_pages": metadata.get("total_pages"),
                    "page_dimensions": {
                        "width_px": metadata.get("page_width_px"),
                        "height_px": metadata.get("page_height_px"),
                    },
                }
            )

        # Add extracted images as base64 if any
        if extracted_images_base64:
            ocr_data["extracted_images"] = extracted_images_base64

        return {
            "ocr_data": ocr_data,
        }
