"""Main OCR service that orchestrates all operations using PaddleOCR vLLM."""

from __future__ import annotations

import base64
import io
import logging
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
        """Call the PaddleOCR pipeline API.

        Uses /v1/infer endpoint which returns structured output with labels
        and bounding boxes from PP-DocLayoutV3 layout detection.
        """
        prompt = self._build_prompt(task=task, custom_prompt=custom_prompt)
        image_url = self._encode_image_base64(image_bytes)

        # Determine if we should extract image crops
        should_include_images = (
            include_images
            if include_images is not None
            else self.default_include_images
        )

        return self._call_infer_endpoint(
            image_url, prompt, image_bytes if should_include_images else None
        )

    def _call_infer_endpoint(
        self,
        image_url: str,
        prompt: str,
        image_bytes: Optional[bytes] = None,
    ) -> Dict[str, Any]:
        """Call the /v1/infer endpoint for structured output with labels.

        Returns structured data including labeled bounding boxes and text.
        """
        payload = {
            "input": [
                {
                    "type": "image_url",
                    "url": image_url,
                }
            ],
            "task": prompt.rstrip(":"),  # Remove trailing colon for task name
        }

        response = self.session.post(
            f"{self.base_url}/v1/infer",
            json=payload,
            timeout=self.timeout,
        )
        response.raise_for_status()
        result = response.json()

        return self._parse_infer_response(result, image_bytes)

    def _parse_infer_response(
        self,
        result: Dict[str, Any],
        image_bytes: Optional[bytes] = None,
    ) -> Dict[str, Any]:
        """Parse /v1/infer response into standard format.

        The pipeline service returns structured data with labeled bounding boxes
        from PP-DocLayoutV3 layout detection.
        """
        bounding_boxes = []
        figure_boxes = []

        # Parse layout detection results (from PP-DocLayoutV3)
        layout_det_res = result.get("layout_det_res", {})
        boxes = layout_det_res.get("boxes", [])

        for box in boxes:
            coord = box.get("coordinate", [])
            if len(coord) >= 4:
                bbox = {
                    "x1": int(coord[0]),
                    "y1": int(coord[1]),
                    "x2": int(coord[2]),
                    "y2": int(coord[3]),
                    "label": box.get("label", "text"),
                    "confidence": float(box.get("score", 1.0)),
                }
                bounding_boxes.append(bbox)

                # Collect figure regions for cropping based on label
                if bbox["label"] in ("image", "figure", "chart", "diagram", "photo"):
                    figure_boxes.append(bbox)

        # Get text and markdown directly from response
        text = result.get("text", "")
        markdown = result.get("markdown", "")

        # Build regions from parsing results
        regions = []
        for block in result.get("parsing_res_list", []):
            region = {
                "label": block.get("block_label", "text"),
                "content": block.get("block_content", ""),
                "bbox": block.get("block_bbox", []),
            }
            # Add image_index for figure regions so crops can be linked
            if region["label"] in ("image", "figure", "chart", "diagram", "photo"):
                region["image_index"] = len([r for r in regions if r.get("image_index") is not None])
            regions.append(region)

        # Extract image crops from figure regions
        crops = []
        if image_bytes and figure_boxes:
            crops = self._extract_figure_crops(image_bytes, figure_boxes)

        return {
            "text": text,
            "markdown": markdown,
            "raw": str(result),
            "bounding_boxes": bounding_boxes,
            "regions": regions,
            "crops": crops,
        }

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
