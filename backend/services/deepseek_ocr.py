import io
import logging
import mimetypes
from typing import Any, Dict, Optional

import config
import requests
from requests import Response
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class DeepSeekOCRError(RuntimeError):
    """Raised when the DeepSeek OCR service returns an error response."""


def _bool_to_str(value: bool) -> str:
    return "true" if value else "false"


class DeepSeekOCRService:
    """HTTP client for the DeepSeek OCR FastAPI service."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> None:
        default_base = config.DEEPSEEK_OCR_URL or "http://localhost:8200"
        self.base_url = (base_url or default_base).rstrip("/")
        self.timeout = timeout or config.DEEPSEEK_OCR_TIMEOUT
        self.logger = logging.getLogger(self.__class__.__name__)

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

    def _url(self, path: str) -> str:
        if not path.startswith("/"):
            path = f"/{path}"
        return f"{self.base_url}{path}"

    def _parse_json(self, response: Response) -> Dict[str, Any]:
        try:
            return response.json()
        except Exception as exc:
            raise DeepSeekOCRError(
                f"Failed to decode DeepSeek OCR response: {exc}"
            ) from exc

    def health_check(self) -> bool:
        """Return True if the OCR service reports healthy."""
        try:
            response = self.session.get(
                self._url("/health"),
                timeout=self.timeout,
            )
            if response.status_code != 200:
                return False
            payload = response.json()
            return bool(payload.get("model_loaded"))
        except Exception as exc:  # pragma: no cover - defensive guard
            self.logger.debug("DeepSeek OCR health check failed: %s", exc)
            return False

    def get_info(self) -> Dict[str, Any]:
        """Retrieve metadata from the OCR service."""
        response = self.session.get(
            self._url("/info"),
            timeout=self.timeout,
        )
        response.raise_for_status()
        return self._parse_json(response)

    def get_presets(self) -> Dict[str, Any]:
        """Retrieve profile/task presets from the OCR service."""
        response = self.session.get(
            self._url("/presets"),
            timeout=self.timeout,
        )
        response.raise_for_status()
        return self._parse_json(response)

    def perform_ocr(
        self,
        *,
        image_bytes: bytes,
        filename: str,
        content_type: Optional[str],
        mode: str,
        prompt: str,
        grounding: bool,
        include_caption: bool,
        find_term: Optional[str],
        schema: Optional[str],
        base_size: int,
        image_size: int,
        crop_mode: bool,
        test_compress: bool,
        profile: Optional[str],
        return_markdown: bool,
        return_figures: bool,
    ) -> Dict[str, Any]:
        """Submit an OCR request to the underlying service."""
        guessed_type, _ = mimetypes.guess_type(filename or "")
        mime = content_type or guessed_type or "application/octet-stream"
        safe_name = filename or "upload.bin"

        files = {
            "image": (safe_name, io.BytesIO(image_bytes), mime),
        }

        data: Dict[str, Any] = {
            "mode": mode,
            "prompt": prompt,
            "grounding": _bool_to_str(grounding),
            "include_caption": _bool_to_str(include_caption),
            "base_size": str(base_size),
            "image_size": str(image_size),
            "crop_mode": _bool_to_str(crop_mode),
            "test_compress": _bool_to_str(test_compress),
            "return_markdown": _bool_to_str(return_markdown),
            "return_figures": _bool_to_str(return_figures),
        }

        if find_term:
            data["find_term"] = find_term
        if schema:
            data["schema"] = schema
        if profile:
            data["profile"] = profile

        try:
            response = self.session.post(
                self._url("/api/ocr"),
                data=data,
                files=files,
                timeout=self.timeout,
            )
        except requests.RequestException as exc:  # pragma: no cover - network guard
            raise DeepSeekOCRError(
                f"Failed to reach DeepSeek OCR service: {exc}"
            ) from exc

        try:
            response.raise_for_status()
        except Exception as exc:
            message = (
                f"DeepSeek OCR returned HTTP {response.status_code}: {response.text}"
            )
            raise DeepSeekOCRError(message) from exc

        payload = self._parse_json(response)

        if not payload.get("success", True):
            raise DeepSeekOCRError(
                payload.get("detail")
                or payload.get("message")
                or "DeepSeek OCR reported failure."
            )

        return payload
