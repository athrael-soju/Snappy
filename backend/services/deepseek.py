import logging
from pathlib import Path
from typing import Any, Dict, Optional

import requests
from config import DEEPSEEK_OCR_API_TIMEOUT, DEEPSEEK_OCR_ENABLED, DEEPSEEK_OCR_URL
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class DeepSeekOCRService:
    """HTTP client for the DeepSeek OCR microservice."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: Optional[int] = None,
        enabled: Optional[bool] = None,
    ):
        self.enabled = enabled if enabled is not None else bool(DEEPSEEK_OCR_ENABLED)
        default_base = DEEPSEEK_OCR_URL or "http://localhost:8200"
        self.base_url = (base_url or default_base).rstrip("/")
        self.timeout = timeout or int(DEEPSEEK_OCR_API_TIMEOUT)

        self._logger = logging.getLogger(__name__)

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
        adapter = HTTPAdapter(max_retries=retry)
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
        mode: str = "plain_ocr",
        prompt: str = "",
        grounding: bool = False,
        include_caption: bool = False,
        find_term: Optional[str] = None,
        json_schema: Optional[str] = None,
        base_size: int = 1024,
        image_size: int = 640,
        crop_mode: bool = True,
        test_compress: bool = False,
    ) -> Dict[str, Any]:
        """Build multipart payload for the /api/ocr endpoint."""
        files = {
            "image": (
                image_path.name,
                image_path.read_bytes(),
                "image/png",
            )
        }
        data = {
            "mode": mode,
            "prompt": prompt,
            "grounding": str(grounding).lower(),
            "include_caption": str(include_caption).lower(),
            "base_size": str(base_size),
            "image_size": str(image_size),
            "crop_mode": str(crop_mode).lower(),
            "test_compress": str(test_compress).lower(),
        }

        if find_term is not None:
            data["find_term"] = find_term
        if json_schema is not None:
            data["json_schema"] = json_schema

        return {"files": files, "data": data}

    def run_ocr(
        self,
        image_path: Path,
        *,
        mode: str = "plain_ocr",
        prompt: str = "",
        grounding: bool = False,
        include_caption: bool = False,
        find_term: Optional[str] = None,
        json_schema: Optional[str] = None,
        base_size: int = 1024,
        image_size: int = 640,
        crop_mode: bool = True,
        test_compress: bool = False,
    ) -> Dict[str, Any]:
        """
        Execute OCR request against the DeepSeek OCR API.

        Returns the JSON response payload from the OCR microservice.
        """
        if not self.enabled:
            raise RuntimeError("DeepSeek OCR service is disabled by configuration.")

        payload = self._prepare_payload(
            image_path,
            mode=mode,
            prompt=prompt,
            grounding=grounding,
            include_caption=include_caption,
            find_term=find_term,
            json_schema=json_schema,
            base_size=base_size,
            image_size=image_size,
            crop_mode=crop_mode,
            test_compress=test_compress,
        )

        response = self.session.post(
            f"{self.base_url}/api/ocr",
            files=payload["files"],
            data=payload["data"],
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()
