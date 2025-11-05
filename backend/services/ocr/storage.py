"""OCR result storage handling."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:  # pragma: no cover - hints only
    from services.minio import MinioService

    from .processor import OcrProcessor

logger = logging.getLogger(__name__)


class OcrStorageHandler:
    """
    Handles persistence of OCR results to MinIO.

    Responsibilities:
    - Format OCR results for storage
    - Upload JSON payloads to MinIO
    - Process and upload extracted images
    - Generate storage URLs
    """

    def __init__(
        self,
        minio_service: "MinioService",
        processor: Optional["OcrProcessor"] = None,
    ):
        """
        Initialize storage handler.

        Args:
            minio_service: MinIO service for uploads
            processor: OCR processor (optional, for image extraction)
        """
        self._minio = minio_service
        self._processor = processor

    def store_ocr_result(
        self,
        ocr_result: Dict[str, Any],
        filename: str,
        page_number: int,
        *,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Store OCR result to MinIO.

        Args:
            ocr_result: Processed OCR result from OcrProcessor
            filename: Document filename
            page_number: Page number
            metadata: Optional additional metadata

        Returns:
            Public URL of stored JSON
        """
        # Process extracted images if processor is available
        extracted_images_urls: List[str] = []
        crops = ocr_result.get("crops", [])

        if crops and self._processor:
            try:
                extracted_images_urls = self._processor.process_extracted_images(
                    crops=crops,
                    filename=filename,
                    page_number=page_number,
                    minio_service=self._minio,
                )

                # Replace base64 in markdown with MinIO URLs
                if extracted_images_urls:
                    markdown = ocr_result.get("markdown", "")
                    ocr_result["markdown"] = self._processor.replace_base64_with_urls(
                        markdown, extracted_images_urls
                    )
            except Exception as exc:
                logger.warning(
                    f"Failed to process extracted images for {filename} page {page_number}: {exc}",
                    exc_info=True,
                )

        # Build storage payload
        payload = {
            "provider": "deepseek-ocr",
            "version": "1.0",
            "filename": filename,
            "page_number": page_number,
            "text": ocr_result.get("text", ""),
            "markdown": ocr_result.get("markdown", ""),
            "raw_text": ocr_result.get("raw_text", ""),
            "text_segments": ocr_result.get("text_segments", []),
            "regions": ocr_result.get("regions", []),
            "extracted_at": datetime.now(timezone.utc).isoformat(),
        }

        # Add metadata if provided
        if metadata:
            payload.update(
                {
                    "document_id": metadata.get("document_id"),
                    "pdf_page_index": metadata.get("pdf_page_index"),
                    "total_pages": metadata.get("total_pages"),
                    "page_dimensions": {
                        "width_px": metadata.get("page_width_px"),
                        "height_px": metadata.get("page_height_px"),
                    },
                    "image": {
                        "url": metadata.get("image_url"),
                        "storage": metadata.get("image_storage"),
                    },
                }
            )

        # Add extracted images metadata if any
        if extracted_images_urls:
            payload["extracted_images"] = [
                {"url": url, "storage": "minio"} for url in extracted_images_urls
            ]

        # Store to MinIO: {filename}/{page_number}/elements.json
        url = self._minio.store_json(
            payload=payload,
            filename=filename,
            page_number=page_number,
            json_filename="elements.json",
        )

        return url

    def fetch_ocr_result(
        self, filename: str, page_number: int
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch OCR result from MinIO if available.

        Args:
            filename: Document filename
            page_number: Page number

        Returns:
            OCR result dictionary or None if not found
        """
        try:
            import json

            # MinIO structure: {filename}/{page_number}/elements.json
            object_name = f"{filename}/{page_number}/elements.json"

            response = self._minio.service.get_object(
                bucket_name=self._minio.bucket_name,
                object_name=object_name,
            )

            return json.loads(response.read())
        except Exception as exc:
            logger.debug(
                f"OCR result not available for {filename} page {page_number}: {exc}"
            )
            return None
