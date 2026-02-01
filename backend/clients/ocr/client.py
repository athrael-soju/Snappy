"""Main OCR service that orchestrates all operations using PaddleOCR vLLM."""

from __future__ import annotations

import base64
import io
import logging
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional

import config
import requests
from PIL import Image
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

if TYPE_CHECKING:  # pragma: no cover - hints only
    from clients.local_storage import LocalStorageClient

from .processor import OcrProcessor

logger = logging.getLogger(__name__)


class OcrClient:
    """Main service class for OCR operations using PaddleOCR vLLM."""

    # Task prompt prefixes for PaddleOCR-VL
    TASK_PROMPTS = {
        "OCR": "OCR:",
        "Table Recognition": "Table Recognition:",
        "Formula Recognition": "Formula Recognition:",
        "Chart Recognition": "Chart Recognition:",
        "Spotting": "Spotting:",
        "Seal Recognition": "Seal Recognition:",
    }

    def __init__(
        self,
        storage_service: Optional["LocalStorageClient"] = None,
        base_url: Optional[str] = None,
        timeout: Optional[int] = None,
        enabled: Optional[bool] = None,
        pool_size: Optional[int] = None,
        default_task: Optional[str] = None,
        include_images: Optional[bool] = None,
    ):
        """Initialize OCR service with all subcomponents.

        Args:
            storage_service: Storage service for image storage
            base_url: PaddleOCR vLLM service URL
            timeout: Request timeout in seconds
            enabled: Enable/disable OCR service
            pool_size: HTTP connection pool size
            default_task: Default OCR task type
            include_images: Default image extraction
        """
        try:
            if storage_service is None:
                raise ValueError("Storage service is required for OcrClient")

            # Initialize HTTP client for PaddleOCR vLLM
            self.enabled = (
                enabled if enabled is not None else bool(config.PADDLE_OCR_ENABLED)
            )
            default_base = config.PADDLE_OCR_URL or "http://localhost:8200"
            self.base_url = (base_url or default_base).rstrip("/")
            self.timeout = timeout or int(config.PADDLE_OCR_API_TIMEOUT)

            # Get configuration values with fallbacks
            if pool_size is None:
                pool_size = getattr(config, "PADDLE_OCR_POOL_SIZE", 20)
            pool_size = max(5, min(100, int(pool_size or 20)))

            # Default processing options
            self.default_task = default_task or getattr(
                config, "PADDLE_OCR_TASK", "OCR"
            )
            self.default_custom_prompt = getattr(config, "PADDLE_OCR_CUSTOM_PROMPT", "")
            self.default_include_images = (
                include_images
                if include_images is not None
                else getattr(config, "PADDLE_OCR_INCLUDE_IMAGES", True)
            )

            # Setup HTTP session with retry logic
            retry = Retry(
                total=3,
                connect=3,
                read=3,
                status=3,
                backoff_factor=0.5,
                status_forcelist=[429, 500, 502, 503, 504],
                allowed_methods={"GET", "POST"},
                raise_on_status=False,
            )
            adapter = HTTPAdapter(
                max_retries=retry,
                pool_connections=pool_size,
                pool_maxsize=pool_size,
            )
            self.session = requests.Session()
            self.session.mount("http://", adapter)
            self.session.mount("https://", adapter)

            # Initialize dependencies
            self.storage_service = storage_service

            # Initialize subcomponents
            from domain.pipeline.image_processor import ImageProcessor

            self.image_processor = ImageProcessor(
                default_format=config.IMAGE_FORMAT,
                default_quality=config.IMAGE_QUALITY,
            )

            self.processor = OcrProcessor(
                ocr_service=self,
                image_processor=self.image_processor,
            )

            # Initialize storage handler
            from domain.ocr_persistence import OcrStorageHandler

            self.storage = OcrStorageHandler(
                storage_service=self.storage_service,
                processor=self.processor,
            )

        except Exception as e:
            raise Exception(f"Failed to initialize OCR service: {e}")

    # HTTP client methods (internal)
    def is_enabled(self) -> bool:
        """Return True when runtime configuration permits OCR usage."""
        return self.enabled

    def _encode_image_base64(self, image_bytes: bytes) -> str:
        """Encode image bytes to base64 data URL."""
        b64 = base64.b64encode(image_bytes).decode("utf-8")
        return f"data:image/png;base64,{b64}"

    def _build_prompt(
        self,
        task: Optional[str] = None,
        custom_prompt: Optional[str] = None,
    ) -> str:
        """Build the prompt for PaddleOCR-VL based on task type."""
        task = task or self.default_task

        if custom_prompt:
            return custom_prompt

        # Get task-specific prompt prefix
        prompt = self.TASK_PROMPTS.get(task, "OCR:")
        return prompt

    def run_ocr(
        self,
        image_path: Path,
        *,
        task: Optional[str] = None,
        custom_prompt: Optional[str] = None,
        include_images: Optional[bool] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Execute OCR request against the PaddleOCR vLLM API."""
        if not self.enabled:
            raise RuntimeError("PaddleOCR service is disabled by configuration.")

        image_bytes = image_path.read_bytes()
        return self._call_vllm_api(
            image_bytes,
            task=task,
            custom_prompt=custom_prompt,
            include_images=include_images,
        )

    def run_ocr_bytes(
        self,
        image_bytes: bytes,
        *,
        filename: str = "page.png",
        task: Optional[str] = None,
        custom_prompt: Optional[str] = None,
        include_images: Optional[bool] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Execute OCR given raw image bytes."""
        if not self.enabled:
            raise RuntimeError("PaddleOCR service is disabled by configuration.")

        return self._call_vllm_api(
            image_bytes,
            task=task,
            custom_prompt=custom_prompt,
            include_images=include_images,
        )

    def run_ocr_image(
        self,
        image: Image.Image,
        *,
        filename: Optional[str] = None,
        format: str = "PNG",
        task: Optional[str] = None,
        custom_prompt: Optional[str] = None,
        include_images: Optional[bool] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Execute OCR directly from a PIL image instance."""
        if not self.enabled:
            raise RuntimeError("PaddleOCR service is disabled by configuration.")

        buffer = io.BytesIO()
        image.save(buffer, format=format)
        return self._call_vllm_api(
            buffer.getvalue(),
            task=task,
            custom_prompt=custom_prompt,
            include_images=include_images,
        )

    def _call_vllm_api(
        self,
        image_bytes: bytes,
        *,
        task: Optional[str] = None,
        custom_prompt: Optional[str] = None,
        include_images: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """Call the PaddleOCR vLLM OpenAI-compatible API.

        The vLLM server exposes an OpenAI-compatible chat completions endpoint.
        We send the image as a base64 data URL in the message content.
        """
        prompt = self._build_prompt(task=task, custom_prompt=custom_prompt)
        image_url = self._encode_image_base64(image_bytes)

        # Build OpenAI-compatible chat completion request
        payload = {
            "model": "PaddleOCR-VL-1.5-0.9B",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": image_url},
                        },
                        {
                            "type": "text",
                            "text": prompt,
                        },
                    ],
                }
            ],
            "max_tokens": 4096,
            "temperature": 0.0,
        }

        response = self.session.post(
            f"{self.base_url}/v1/chat/completions",
            json=payload,
            timeout=self.timeout,
        )
        response.raise_for_status()
        result = response.json()

        # Extract the generated text from OpenAI response format
        generated_text = ""
        if "choices" in result and len(result["choices"]) > 0:
            message = result["choices"][0].get("message", {})
            generated_text = message.get("content", "")

        # Determine if we should extract image crops
        should_include_images = (
            include_images
            if include_images is not None
            else self.default_include_images
        )

        # Parse the response into our standard format
        return self._parse_ocr_response(
            generated_text,
            task=task,
            image_bytes=image_bytes if should_include_images else None,
        )

    def _parse_ocr_response(
        self,
        generated_text: str,
        task: Optional[str] = None,
        image_bytes: Optional[bytes] = None,
    ) -> Dict[str, Any]:
        """Parse PaddleOCR vLLM response into standard format.

        PaddleOCR-VL outputs markdown-formatted text with optional bounding boxes.
        The format varies by task type. If image_bytes is provided, figure regions
        are cropped and returned as base64-encoded images.
        """
        import re

        task = task or self.default_task
        text = generated_text.strip()

        # Extract bounding boxes if present (format: [[x1,y1],[x2,y2],[x3,y3],[x4,y4]])
        bounding_boxes = []

        # Pattern for 4-point bounding boxes in PaddleOCR format
        bbox_pattern = r'\[\[(\d+),(\d+)\],\[(\d+),(\d+)\],\[(\d+),(\d+)\],\[(\d+),(\d+)\]\]'
        matches = re.findall(bbox_pattern, text)

        for match in matches:
            coords = [int(c) for c in match]
            # Convert 4-point polygon to rectangular bbox (x1, y1, x2, y2)
            x_coords = [coords[0], coords[2], coords[4], coords[6]]
            y_coords = [coords[1], coords[3], coords[5], coords[7]]
            bounding_boxes.append({
                "x1": min(x_coords),
                "y1": min(y_coords),
                "x2": max(x_coords),
                "y2": max(y_coords),
                "label": "text",
            })

        # Clean text by removing bbox coordinates for markdown output
        clean_text = re.sub(bbox_pattern, '', text).strip()

        # Detect figure references in markdown (e.g., ![Figure 1], ![Image], etc.)
        figure_boxes = self._detect_figure_regions(clean_text, bounding_boxes)

        # Extract image crops if we have figure regions and original image
        crops = []
        if image_bytes and figure_boxes:
            crops = self._extract_figure_crops(image_bytes, figure_boxes)

        return {
            "text": clean_text,
            "markdown": clean_text,
            "raw": text,
            "bounding_boxes": bounding_boxes,
            "crops": crops,
        }

    def _detect_figure_regions(
        self,
        markdown_text: str,
        bounding_boxes: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Detect figure/image regions from markdown content and bounding boxes.

        Looks for figure references in markdown and marks corresponding regions.
        Also identifies large regions that are likely figures based on aspect ratio.
        """
        import re

        figure_boxes = []

        # Pattern for figure references: ![Figure N], ![Image], ![Diagram], etc.
        figure_pattern = r'!\[(Figure|Image|Diagram|Chart|Graph|Photo|Picture)\s*\d*\]'
        figure_matches = re.findall(figure_pattern, markdown_text, re.IGNORECASE)

        # If we have figure references but no explicit figure bounding boxes,
        # try to identify figure regions by their characteristics
        if figure_matches and bounding_boxes:
            # Heuristic: figures tend to be larger, more square regions
            for bbox in bounding_boxes:
                width = bbox["x2"] - bbox["x1"]
                height = bbox["y2"] - bbox["y1"]
                area = width * height
                aspect_ratio = width / max(height, 1)

                # Mark as figure if:
                # - Large area (> 10000 sq px)
                # - Relatively square aspect ratio (0.5 to 2.0)
                if area > 10000 and 0.3 <= aspect_ratio <= 3.0:
                    figure_box = bbox.copy()
                    figure_box["label"] = "figure"
                    figure_boxes.append(figure_box)

        return figure_boxes

    def _extract_figure_crops(
        self,
        image_bytes: bytes,
        figure_boxes: List[Dict[str, Any]],
    ) -> List[str]:
        """Extract figure regions from the original image as base64 crops.

        Args:
            image_bytes: Original image bytes
            figure_boxes: List of bounding boxes for figure regions

        Returns:
            List of base64-encoded cropped images
        """
        crops = []

        try:
            # Load the original image
            original_image = Image.open(io.BytesIO(image_bytes))
            img_width, img_height = original_image.size

            for bbox in figure_boxes:
                try:
                    # Ensure coordinates are within image bounds
                    x1 = max(0, min(bbox["x1"], img_width))
                    y1 = max(0, min(bbox["y1"], img_height))
                    x2 = max(0, min(bbox["x2"], img_width))
                    y2 = max(0, min(bbox["y2"], img_height))

                    # Skip if region is too small
                    if (x2 - x1) < 10 or (y2 - y1) < 10:
                        continue

                    # Crop the region
                    cropped = original_image.crop((x1, y1, x2, y2))

                    # Convert to base64
                    buffer = io.BytesIO()
                    cropped.save(buffer, format="PNG")
                    crop_b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
                    crops.append(crop_b64)

                except Exception as crop_exc:
                    logger.warning(f"Failed to crop figure region: {crop_exc}")
                    continue

        except Exception as exc:
            logger.warning(f"Failed to extract figure crops: {exc}")

        return crops

    # Public orchestration methods

    def health_check(self) -> bool:
        """Check if OCR service is healthy and accessible."""
        if not self.enabled:
            logger.debug("Skipping PaddleOCR health check: service disabled")
            return False
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=self.timeout)
            response.raise_for_status()
            return True
        except Exception as exc:
            logger.warning("PaddleOCR health check failed: %s", exc)
            return False

    def restart(self) -> bool:
        """Request service restart to stop any ongoing processing.

        Note: The PaddleOCR vLLM container may not support restart endpoint.
        Returns False as restart is typically handled by Docker.
        """
        if not self.enabled:
            logger.debug("Skipping PaddleOCR restart: service disabled")
            return False

        logger.info("PaddleOCR restart requested - container restart needed")
        return False

    def close(self):
        """Close the HTTP session and release connections."""
        if hasattr(self, "session"):
            self.session.close()

    def __del__(self):
        """Ensure session is closed on garbage collection."""
        self.close()
