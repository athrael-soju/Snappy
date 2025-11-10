"""OCR result storage handling."""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:  # pragma: no cover - hints only
    from services.duckdb_service import DuckDBService
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
        duckdb_service: Optional["DuckDBService"] = None,
    ):
        """
        Initialize storage handler.

        Args:
            minio_service: MinIO service for uploads
            processor: OCR processor (optional, for image extraction)
            duckdb_service: DuckDB service for structured storage (optional)
        """
        self._minio = minio_service
        self._processor = processor
        self._duckdb = duckdb_service

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
        regions = ocr_result.get("regions", [])

        if crops and self._processor:
            try:
                extracted_images_urls = self._processor.process_extracted_images(
                    crops=crops,
                    filename=filename,
                    page_number=page_number,
                    minio_service=self._minio,
                )

                # Replace base64 image data with MinIO URLs in markdown/text
                if extracted_images_urls:
                    for field in ("markdown", "text"):
                        content = ocr_result.get(field, "")
                        if content:
                            ocr_result[field] = (
                                self._processor.replace_base64_with_urls(
                                    content, extracted_images_urls
                                )
                            )
            except Exception as exc:
                logger.warning(
                    f"Failed to process extracted images for {filename} page {page_number}: {exc}",
                    exc_info=True,
                )

        # Attach extracted image metadata to regions when available
        if regions:
            for region in regions:
                image_idx = region.pop("image_index", None)
                if isinstance(image_idx, int) and 0 <= image_idx < len(
                    extracted_images_urls
                ):
                    region["image_url"] = extracted_images_urls[image_idx]
                    region["image_storage"] = "minio"
                    region["image_inline"] = False

        figure_url_map = {idx + 1: url for idx, url in enumerate(extracted_images_urls)}
        if figure_url_map:
            for field in ("markdown", "text"):
                ocr_result[field] = self._ensure_figure_links(
                    ocr_result.get(field, ""), figure_url_map
                )

        json_filename = "elements.json"
        object_name = f"{filename}/{page_number}/{json_filename}"
        storage_url = self._minio._get_image_url(object_name)

        # Build storage payload
        payload = {
            "provider": "deepseek-ocr",
            "version": "1.0",
            "filename": filename,
            "page_number": page_number,
            "text": ocr_result.get("text", ""),
            "markdown": ocr_result.get("markdown", ""),
            "raw_text": ocr_result.get("raw_text", ""),
            "regions": regions,
            "extracted_at": datetime.now(timezone.utc).isoformat(),
            "storage_url": storage_url,
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
            json_filename=json_filename,
        )

        # Also store to DuckDB for quantitative searching
        if self._duckdb and self._duckdb.enabled:
            try:
                self._duckdb.store_ocr_result(payload)
                logger.debug(
                    f"Stored OCR result to DuckDB: {filename} page {page_number}"
                )
            except Exception as e:
                logger.warning(
                    f"Failed to store OCR result to DuckDB: {e}", exc_info=True
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

    @staticmethod
    def _ensure_figure_links(content: str, figure_map: Dict[int, str]) -> str:
        """Ensure figure references point to hosted URLs and append any missing links."""
        if not figure_map:
            return content or ""

        content = content or ""

        def replace_markdown(match: re.Match[str]) -> str:
            figure_num = int(match.group(1))
            url = figure_map.get(figure_num)
            if not url:
                return match.group(0)
            return f"![Figure {figure_num}]({url})"

        updated = re.sub(r"!\[Figure (\d+)\]\(([^)]*)\)", replace_markdown, content)

        def replace_bare(match: re.Match[str]) -> str:
            figure_num = int(match.group(1))
            url = figure_map.get(figure_num)
            if not url:
                return match.group(0)
            return f"![Figure {figure_num}]({url})"

        updated = re.sub(r"!\[Figure (\d+)\](?!\()", replace_bare, updated)

        referenced = {
            int(m.group(1))
            for m in re.finditer(r"!\[Figure (\d+)\]", updated)
            if m.group(1).isdigit()
        }

        missing = [num for num in figure_map if num not in referenced]
        if missing:
            additions = "\n".join(
                f"![Figure {num}]({figure_map[num]})" for num in missing
            )
            base = updated.strip()
            if base:
                updated = f"{base}\n\n{additions}"
            else:
                updated = additions

        return updated.strip()
