"""
Lightweight clients for benchmark execution.

These clients wrap the service APIs without requiring storage dependencies.
"""

import io
import logging
import re
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from PIL import Image
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class BenchmarkColPaliClient:
    """Lightweight ColPali client for benchmarking."""

    def __init__(self, base_url: str = "http://localhost:7000", timeout: int = 60):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

        # Setup session with retries
        retry = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry)
        self.session = requests.Session()
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def health_check(self) -> bool:
        """Check if the service is healthy."""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    def generate_interpretability_maps(
        self, query: str, image: Image.Image
    ) -> Dict[str, Any]:
        """Generate interpretability maps for a query-image pair.

        Args:
            query: The query text
            image: PIL Image to analyze

        Returns:
            Dictionary with similarity_maps, n_patches_x, n_patches_y, etc.
        """
        img_buffer = io.BytesIO()
        image.save(img_buffer, format="PNG")
        img_buffer.seek(0)

        try:
            files = {"file": ("image.png", img_buffer, "image/png")}
            data = {"query": query}

            response = self.session.post(
                f"{self.base_url}/interpret",
                data=data,
                files=files,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()
        finally:
            img_buffer.close()


class BenchmarkOcrClient:
    """Lightweight OCR client for benchmarking."""

    def __init__(
        self,
        base_url: str = "http://localhost:8200",
        timeout: int = 120,
        mode: str = "Gundam",
        task: str = "markdown",
        include_grounding: bool = True,
        include_images: bool = True,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.mode = mode
        self.task = task
        self.include_grounding = include_grounding
        self.include_images = include_images

        # Setup session with retries
        retry = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry)
        self.session = requests.Session()
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def health_check(self) -> bool:
        """Check if the service is healthy."""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    def process_image(
        self,
        image: Image.Image,
        *,
        mode: Optional[str] = None,
        task: Optional[str] = None,
        include_grounding: Optional[bool] = None,
        include_images: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """Process an image through OCR.

        Args:
            image: PIL Image to process
            mode: OCR mode (default: Gundam)
            task: OCR task (default: markdown)
            include_grounding: Whether to include bounding boxes
            include_images: Whether to include extracted image crops

        Returns:
            OCR result with markdown content and optional grounding
        """
        mode = mode or self.mode
        task = task or self.task
        include_grounding = (
            include_grounding if include_grounding is not None else self.include_grounding
        )
        include_images = (
            include_images if include_images is not None else self.include_images
        )

        # Convert PIL image to bytes
        img_buffer = io.BytesIO()
        image.save(img_buffer, format="PNG")
        img_bytes = img_buffer.getvalue()

        # Write to temp file (required by the API)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
            tmp.write(img_bytes)
            tmp_path = Path(tmp.name)

        try:
            files = {"image": (tmp_path.name, tmp_path.read_bytes(), "image/png")}
            data = {
                "mode": mode,
                "task": task,
                "include_grounding": str(include_grounding).lower(),
                "include_images": str(include_images).lower(),
            }

            response = self.session.post(
                f"{self.base_url}/api/ocr",
                files=files,
                data=data,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()
        finally:
            try:
                tmp_path.unlink()
            except OSError:
                pass

    def extract_regions(self, ocr_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract regions from OCR result.

        Converts bounding_boxes data to a list of region dictionaries.
        Extracts actual text content from the raw OCR output by parsing
        grounding references.

        Args:
            ocr_result: Raw OCR API response

        Returns:
            List of regions with id, label, bbox, and content
        """
        regions = []

        # The OCR API returns bounding_boxes as a list of items with x1,y1,x2,y2 keys
        bounding_boxes = ocr_result.get("bounding_boxes", [])

        # Extract content mapping from raw text (like Snappy backend does)
        raw_text = ocr_result.get("raw", "")
        content_map = self._extract_region_content(raw_text) if raw_text else {}

        for idx, item in enumerate(bounding_boxes):
            # Handle both formats: {x1, y1, x2, y2} or {bbox: [x1, y1, x2, y2]}
            if "bbox" in item:
                bbox = item["bbox"]
            elif all(k in item for k in ("x1", "y1", "x2", "y2")):
                bbox = [item["x1"], item["y1"], item["x2"], item["y2"]]
            else:
                continue

            # Label is the type (text, table, image, etc.)
            label = item.get("label", "unknown")

            # Get content from the content map if available
            content = ""
            if label in content_map and content_map[label]:
                content = content_map[label].pop(0)

            if len(bbox) == 4:
                regions.append({
                    "id": f"region-{idx}",
                    "label": label,
                    "bbox": bbox,  # [x1, y1, x2, y2] in pixels
                    "content": content,  # Extracted text content
                })

        return regions

    def _extract_region_content(self, raw_text: str) -> Dict[str, List[str]]:
        """
        Extract content for each labeled region from raw OCR output.

        The raw text contains patterns like:
        <|ref|>label<|/ref|><|det|>[[coords]]<|/det|>
        Content here

        This mirrors the logic in Snappy backend's OcrProcessor.

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
