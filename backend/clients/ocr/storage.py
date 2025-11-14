"""OCR result storage handling."""

from __future__ import annotations

import logging
import re
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:  # pragma: no cover - hints only
    from clients.duckdb import DuckDBService
    from clients.minio import MinioService

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
            duckdb_service: DuckDB service (optional, for analytics storage)
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
    ) -> Dict[str, Any]:
        """
        Store OCR result to MinIO with UUID-based naming.

        Args:
            ocr_result: Processed OCR result from OcrProcessor
            filename: Document filename
            page_number: Page number
            metadata: Optional additional metadata

        Returns:
            Dictionary with ocr_url and ocr_regions array:
            {
                "ocr_url": "URL to full OCR JSON",
                "ocr_regions": [{"label": "text", "url": "...", "id": "..."}, ...]
            }
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

        # Generate UUIDs for regions and store individual region JSON files
        ocr_regions_metadata: List[Dict[str, str]] = []
        if regions:
            for idx, region in enumerate(regions):
                # Generate unique ID for this region
                region_id = str(uuid.uuid4())
                region["id"] = region_id

                # Attach extracted image metadata if available
                image_idx = region.pop("image_index", None)
                if isinstance(image_idx, int) and 0 <= image_idx < len(
                    extracted_images_urls
                ):
                    region["image_url"] = extracted_images_urls[image_idx]
                    region["image_storage"] = "minio"
                    region["image_inline"] = False

                # Store individual region JSON file in ocr_regions/ subfolder
                region_json_filename = f"ocr_regions/region_{region_id}.json"

                region_payload = {
                    "id": region_id,
                    "label": region.get("label", "unknown"),
                    "bbox": region.get("bbox", []),
                    "content": region.get("content", ""),
                }

                try:
                    region_url = self._minio.store_json(
                        payload=region_payload,
                        filename=filename,
                        page_number=page_number,
                        json_filename=region_json_filename,
                    )

                    # Build metadata for Qdrant payload
                    ocr_regions_metadata.append(
                        {
                            "label": region.get("label", "unknown"),
                            "url": region_url,
                            "id": region_id,
                        }
                    )
                except Exception as exc:
                    logger.warning(f"Failed to store region {region_id} JSON: {exc}")

        figure_url_map = {idx + 1: url for idx, url in enumerate(extracted_images_urls)}
        if figure_url_map:
            for field in ("markdown", "text"):
                ocr_result[field] = self._ensure_figure_links(
                    ocr_result.get(field, ""), figure_url_map
                )

        # Generate UUID for full OCR JSON file in ocr/ subfolder
        ocr_uuid = str(uuid.uuid4())
        json_filename = f"ocr/{ocr_uuid}.json"
        object_name = f"{filename}/{page_number}/{json_filename}"
        storage_url = self._minio._get_image_url(object_name)

        # Build storage payload
        payload = {
            "id": ocr_uuid,
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

        # Store full OCR JSON to MinIO with UUID name
        url = self._minio.store_json(
            payload=payload,
            filename=filename,
            page_number=page_number,
            json_filename=json_filename,
        )

        # Store to DuckDB if enabled (non-blocking)
        if self._duckdb and self._duckdb.is_enabled():
            try:
                self._duckdb.store_ocr_page(
                    provider=payload.get("provider", "deepseek-ocr"),
                    version=payload.get("version", "1.0"),
                    filename=filename,
                    page_number=page_number,
                    text=payload.get("text", ""),
                    markdown=payload.get("markdown", ""),
                    raw_text=payload.get("raw_text"),
                    regions=payload.get("regions", []),
                    extracted_at=payload.get("extracted_at", ""),
                    storage_url=url,
                    document_id=payload.get("document_id"),
                    pdf_page_index=payload.get("pdf_page_index"),
                    total_pages=payload.get("total_pages"),
                    page_width_px=(
                        payload.get("page_dimensions", {}).get("width_px")
                        if metadata
                        else None
                    ),
                    page_height_px=(
                        payload.get("page_dimensions", {}).get("height_px")
                        if metadata
                        else None
                    ),
                    image_url=(
                        payload.get("image", {}).get("url") if metadata else None
                    ),
                    image_storage=(
                        payload.get("image", {}).get("storage") if metadata else None
                    ),
                    extracted_images=payload.get("extracted_images", []),
                )
            except Exception as exc:
                logger.warning(
                    f"Failed to store OCR result in DuckDB (non-blocking): {exc}"
                )

        return {
            "ocr_url": url,
            "ocr_regions": ocr_regions_metadata,
        }

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

        Note:
            This method is deprecated with UUID-based storage. Use the ocr_url
            from Qdrant payload instead of constructing the path.
        """
        try:
            import json

            # List files in ocr/ subfolder
            prefix = f"{filename}/{page_number}/ocr/"

            for obj in self._minio.service.list_objects(
                bucket_name=self._minio.bucket_name,
                prefix=prefix,
            ):
                obj_name = getattr(obj, "object_name", "")
                if obj_name and obj_name.endswith(".json"):
                    # Found OCR JSON
                    response = self._minio.service.get_object(
                        bucket_name=self._minio.bucket_name,
                        object_name=obj_name,
                    )
                    return json.loads(response.read())

            # No OCR result found
            logger.warning(
                f"OCR result not found for {filename} page {page_number} in ocr/ subfolder"
            )
            return None

        except Exception as exc:
            logger.error(
                f"Failed to fetch OCR result for {filename} page {page_number}: {exc}",
                exc_info=True,
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
