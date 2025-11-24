"""OCR result storage handling."""

from __future__ import annotations

import logging
import re
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:  # pragma: no cover - hints only
    from clients.duckdb import DuckDBClient
    from clients.minio import MinioClient

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
        minio_service: "MinioClient",
        processor: Optional["OcrProcessor"] = None,
        duckdb_service: Optional["DuckDBClient"] = None,
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
        document_id: str,
        page_number: int,
        *,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Store OCR result to MinIO with UUID-based naming.

        Args:
            ocr_result: Processed OCR result from OcrProcessor
            document_id: Document UUID for storage paths
            page_number: Page number
            metadata: Optional additional metadata (should include 'filename' for display)

        Returns:
            Dictionary with ocr_url and ocr_regions array:
            {
                "ocr_url": "URL to full OCR JSON",
                "ocr_regions": [{"label": "text", "url": "...", "id": "..."}, ...]
            }
        """
        # Extract filename from metadata for logging/payload (not for paths)
        filename = metadata.get("filename") if metadata else None

        # Process extracted images if processor is available
        extracted_images_urls: List[str] = []
        crops = ocr_result.get("crops", [])
        regions = ocr_result.get("regions", [])

        if crops and self._processor:
            try:
                extracted_images_urls = self._processor.process_extracted_images(
                    crops=crops,
                    document_id=document_id,
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
                    f"Failed to process extracted images for document {document_id} page {page_number}: {exc}",
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
                        document_id=document_id,
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
        object_name = f"{document_id}/{page_number}/{json_filename}"
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
                    "page_id": metadata.get("page_id"),
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
            document_id=document_id,
            page_number=page_number,
            json_filename=json_filename,
        )

        # Store to DuckDB if enabled (non-blocking)
        if self._duckdb and self._duckdb.is_enabled():
            try:
                success = self._duckdb.store_ocr_page(
                    provider=payload.get("provider", "deepseek-ocr"),
                    version=payload.get("version", "1.0"),
                    filename=str(filename) if filename is not None else "",
                    page_number=page_number,
                    page_id=payload["page_id"],  # Required - Pydantic validates
                    document_id=payload["document_id"],  # Required - Pydantic validates
                    text=payload.get("text", ""),
                    markdown=payload.get("markdown", ""),
                    raw_text=payload.get("raw_text"),
                    regions=payload.get("regions", []),
                    extracted_at=payload.get("extracted_at", ""),
                    storage_url=url,
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
                if not success:
                    error_msg = (
                        f"DuckDB storage returned False for {filename} page {page_number}. "
                        "This indicates a critical storage failure."
                    )
                    logger.error(error_msg)
                    raise RuntimeError(error_msg)
            except KeyError as exc:
                logger.error(
                    f"Missing required field {exc} in payload for {filename} page {page_number}. "
                    "This is a schema validation error - check that metadata includes all required fields.",
                    exc_info=True
                )
                raise
            except RuntimeError:
                # Re-raise RuntimeError from success=False case
                raise
            except Exception as exc:
                logger.error(
                    f"Failed to store OCR result in DuckDB for {filename} page {page_number}: {exc}. "
                    "This is a critical error that must be fixed.",
                    exc_info=True
                )
                raise

        return {
            "ocr_url": url,
            "ocr_regions": ocr_regions_metadata,
        }

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
