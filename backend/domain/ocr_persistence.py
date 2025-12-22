"""OCR result storage handling."""

from __future__ import annotations

import logging
import re
import uuid
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:  # pragma: no cover - hints only
    from clients.local_storage import LocalStorageClient
    from clients.ocr.processor import OcrProcessor

logger = logging.getLogger(__name__)


class OcrStorageHandler:
    """
    Handles persistence of OCR extracted images to local storage.

    OCR text/markdown/regions are stored inline in Qdrant payloads.
    This handler only stores extracted images (figures, diagrams, etc.)
    and attaches their URLs to region data.
    """

    def __init__(
        self,
        storage_service: "LocalStorageClient",
        processor: Optional["OcrProcessor"] = None,
    ):
        """
        Initialize storage handler.

        Args:
            storage_service: Storage service for uploads
            processor: OCR processor (optional, for image extraction)
        """
        self._storage = storage_service
        self._processor = processor

    def store_ocr_result(
        self,
        ocr_result: Dict[str, Any],
        document_id: str,
        page_number: int,
        *,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Process and store extracted images, updating regions with image URLs.

        OCR text/markdown/regions are stored inline in Qdrant payloads.
        This method only handles:
        1. Uploading extracted images (figures, diagrams) to local storage
        2. Updating region data with image URLs
        3. Replacing base64 image data in markdown/text with storage URLs

        The ocr_result dict is modified in-place to include image URLs.

        Args:
            ocr_result: Processed OCR result from OcrProcessor (modified in-place)
            document_id: Document UUID for storage paths
            page_number: Page number
            metadata: Optional additional metadata
        """
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
                    storage_service=self._storage,
                )

                # Replace base64 image data with storage URLs in markdown/text
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

        # Attach image URLs to regions (regions stored inline in Qdrant, not as separate files)
        if regions:
            for region in regions:
                # Generate unique ID for this region
                region["id"] = str(uuid.uuid4())

                # Attach extracted image URL if available
                image_idx = region.pop("image_index", None)
                if isinstance(image_idx, int) and 0 <= image_idx < len(
                    extracted_images_urls
                ):
                    region["image_url"] = extracted_images_urls[image_idx]

        # Ensure figure links in markdown/text point to storage URLs
        figure_url_map = {idx + 1: url for idx, url in enumerate(extracted_images_urls)}
        if figure_url_map:
            for field in ("markdown", "text"):
                ocr_result[field] = self._ensure_figure_links(
                    ocr_result.get(field, ""), figure_url_map
                )

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
