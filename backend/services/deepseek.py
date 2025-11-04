import io
import logging
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

# Import config dynamically to support runtime updates
import config
import requests
from config import DEEPSEEK_OCR_API_TIMEOUT, DEEPSEEK_OCR_ENABLED, DEEPSEEK_OCR_URL
from PIL import Image
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class DeepSeekOCRService:
    """HTTP client for the DeepSeek OCR microservice."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: Optional[int] = None,
        enabled: Optional[bool] = None,
        pool_size: Optional[int] = None,
        default_mode: Optional[str] = None,
        default_task: Optional[str] = None,
        include_grounding: Optional[bool] = None,
        include_images: Optional[bool] = None,
    ):
        self.enabled = enabled if enabled is not None else bool(DEEPSEEK_OCR_ENABLED)
        default_base = DEEPSEEK_OCR_URL or "http://localhost:8200"
        self.base_url = (base_url or default_base).rstrip("/")
        self.timeout = timeout or int(DEEPSEEK_OCR_API_TIMEOUT)

        self._logger = logging.getLogger(__name__)

        # Get configuration values with fallbacks
        if pool_size is None:
            pool_size = getattr(config, "DEEPSEEK_OCR_POOL_SIZE", 20)
        pool_size = max(5, min(100, int(pool_size or 20)))  # Clamp to valid range

        # Default processing options
        self.default_mode = default_mode or getattr(
            config, "DEEPSEEK_OCR_MODE", "Gundam"
        )
        self.default_task = default_task or getattr(
            config, "DEEPSEEK_OCR_TASK", "markdown"
        )
        self.default_locate_text = getattr(config, "DEEPSEEK_OCR_LOCATE_TEXT", "")
        self.default_custom_prompt = getattr(config, "DEEPSEEK_OCR_CUSTOM_PROMPT", "")
        self.default_include_grounding = (
            include_grounding
            if include_grounding is not None
            else getattr(config, "DEEPSEEK_OCR_INCLUDE_GROUNDING", True)
        )
        self.default_include_images = (
            include_images
            if include_images is not None
            else getattr(config, "DEEPSEEK_OCR_INCLUDE_IMAGES", True)
        )

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
        # Increase pool size to handle concurrent OCR requests (workers × retries)
        adapter = HTTPAdapter(
            max_retries=retry,
            pool_connections=pool_size,  # Number of connection pools to cache
            pool_maxsize=pool_size,  # Max connections per pool
        )
        self.session = requests.Session()
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def is_enabled(self) -> bool:
        """Return True when runtime configuration permits OCR usage."""
        return self.enabled

    def health_check(self) -> bool:
        """Ping the DeepSeek OCR health endpoint."""
        if not self.enabled:
            self._logger.debug("Skipping DeepSeek health check: service disabled")
            return False
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=self.timeout)
            response.raise_for_status()
            payload = response.json()
            return bool(payload.get("status") == "healthy")
        except Exception as exc:
            self._logger.warning("DeepSeek OCR health check failed: %s", exc)
            return False

    def _prepare_payload(
        self,
        image_path: Path,
        *,
        mode: Optional[str] = None,
        task: Optional[str] = None,
        custom_prompt: Optional[str] = None,
        include_grounding: Optional[bool] = None,
        include_images: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """Build multipart payload for the /api/ocr endpoint."""
        # Use instance defaults if not provided
        mode = mode or self.default_mode
        task = task or self.default_task
        include_grounding = (
            include_grounding
            if include_grounding is not None
            else self.default_include_grounding
        )
        include_images = (
            include_images
            if include_images is not None
            else self.default_include_images
        )

        # Auto-populate custom_prompt based on task type if not explicitly provided
        if custom_prompt is None:
            if task == "locate" and self.default_locate_text:
                custom_prompt = self.default_locate_text
            elif task == "custom" and self.default_custom_prompt:
                custom_prompt = self.default_custom_prompt

        files = {
            "image": (
                image_path.name,
                image_path.read_bytes(),
                "image/png",
            )
        }
        data = {
            "mode": mode,
            "task": task,
            "include_grounding": str(include_grounding).lower(),
            "include_images": str(include_images).lower(),
        }

        if custom_prompt is not None:
            data["custom_prompt"] = custom_prompt

        return {"files": files, "data": data}

    def run_ocr(
        self,
        image_path: Path,
        *,
        mode: Optional[str] = None,
        task: Optional[str] = None,
        custom_prompt: Optional[str] = None,
        include_grounding: Optional[bool] = None,
        include_images: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        Execute OCR request against the DeepSeek OCR API.

        Args:
            image_path: Path to image file
            mode: Processing mode (Gundam, Tiny, Small, Base, Large) - uses default if not specified
            task: Task type (markdown, plain_ocr, locate, describe, custom) - uses default if not specified
            custom_prompt: Custom prompt for custom/locate tasks
            include_grounding: Include bounding box information - uses default if not specified
            include_images: Extract and embed images - uses default if not specified

        Returns the JSON response payload from the OCR microservice.
        """
        if not self.enabled:
            raise RuntimeError("DeepSeek OCR service is disabled by configuration.")

        payload = self._prepare_payload(
            image_path,
            mode=mode,
            task=task,
            custom_prompt=custom_prompt,
            include_grounding=include_grounding,
            include_images=include_images,
        )

        response = self.session.post(
            f"{self.base_url}/api/ocr",
            files=payload["files"],
            data=payload["data"],
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------
    def run_ocr_bytes(
        self,
        image_bytes: bytes,
        *,
        filename: str = "page.png",
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Execute OCR given raw image bytes by spilling to a temporary file."""
        if not self.enabled:
            raise RuntimeError("DeepSeek OCR service is disabled by configuration.")

        suffix = Path(filename).suffix or ".png"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(image_bytes)
            tmp_path = Path(tmp.name)
        try:
            return self.run_ocr(tmp_path, **kwargs)
        finally:
            try:
                tmp_path.unlink()
            except OSError:
                pass

    def run_ocr_image(
        self,
        image: Image.Image,
        *,
        filename: Optional[str] = None,
        format: str = "PNG",
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Execute OCR directly from a PIL image instance."""
        if not self.enabled:
            raise RuntimeError("DeepSeek OCR service is disabled by configuration.")

        buffer = io.BytesIO()
        image.save(buffer, format=format)
        return self.run_ocr_bytes(
            buffer.getvalue(),
            filename=filename or f"page.{format.lower()}",
            **kwargs,
        )

    def close(self):
        """Close the HTTP session and release connections."""
        if hasattr(self, "session"):
            self.session.close()

    def __del__(self):
        """Ensure session is closed on garbage collection."""
        self.close()
