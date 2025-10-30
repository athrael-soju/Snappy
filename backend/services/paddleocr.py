from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import config
import requests
from requests import Response
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class PaddleOCRServiceError(RuntimeError):
    """Raised when the PaddleOCR-VL service returns an error."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        payload: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.status_code = status_code or 500
        self.payload = payload or {}


class PaddleOCRService:
    """HTTP client for the PaddleOCR-VL microservice."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_prefix: Optional[str] = None,
        timeout: Optional[int] = None,
        max_file_mb: Optional[int] = None,
    ):
        self.enabled: bool = bool(getattr(config, "PADDLE_OCR_ENABLED", False))
        default_url = getattr(config, "PADDLE_OCR_URL", "http://localhost:8100")
        default_prefix = getattr(config, "PADDLE_OCR_API_PREFIX", "/api/v1")
        default_timeout = int(getattr(config, "PADDLE_OCR_TIMEOUT", 300))
        default_max_mb = int(getattr(config, "PADDLE_OCR_MAX_FILE_MB", 50))

        self.base_url = (base_url or default_url).rstrip("/")
        self.api_prefix = (api_prefix or default_prefix).strip("/")
        self.timeout = int(timeout) if timeout is not None else default_timeout
        self.max_file_bytes = (
            max(1, int(max_file_mb) if max_file_mb is not None else default_max_mb)
            * 1024
            * 1024
        )

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

    def _build_url(self, path: str, *, include_prefix: bool = True) -> str:
        base = self.base_url
        if include_prefix and self.api_prefix:
            return f"{base}/{self.api_prefix.strip('/')}/{path.lstrip('/')}"
        return f"{base}/{path.lstrip('/')}"

    def _request(self, method: str, url: str, **kwargs) -> Response:
        try:
            response = self.session.request(method, url, timeout=self.timeout, **kwargs)
        except requests.RequestException as exc:  # pragma: no cover - network failure
            raise PaddleOCRServiceError(f"PaddleOCR-VL request failed: {exc}") from exc

        if response.status_code >= 400:
            message = f"PaddleOCR-VL error ({response.status_code})"
            payload: Dict[str, Any] | None = None
            try:
                payload = response.json()
                detail = payload.get("detail") or payload.get("message")
                if detail:
                    message = f"{message}: {detail}"
            except Exception:
                detail = response.text.strip()
                if detail:
                    message = f"{message}: {detail}"

            raise PaddleOCRServiceError(
                message,
                status_code=response.status_code,
                payload=payload or {},
            )

        return response

    def ensure_enabled(self) -> None:
        if not self.enabled:
            raise PaddleOCRServiceError(
                "PaddleOCR-VL integration is disabled.", status_code=503
            )

    def health(self) -> Dict[str, Any]:
        """Fetch service health information."""
        url = self._build_url("health", include_prefix=False)
        response = self._request("GET", url)
        try:
            return response.json()
        except ValueError as exc:
            raise PaddleOCRServiceError(
                "Invalid health response from PaddleOCR-VL"
            ) from exc

    def service_info(self) -> Dict[str, Any]:
        """Fetch root metadata exposed by the service."""
        url = self._build_url("", include_prefix=False)
        response = self._request("GET", url)
        try:
            return response.json()
        except ValueError:
            return {}

    def extract_document(
        self,
        *,
        file_bytes: bytes,
        filename: Optional[str] = None,
        content_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Run OCR against a binary document and return structured results.
        """
        self.ensure_enabled()

        if not file_bytes:
            raise PaddleOCRServiceError("Upload is empty.", status_code=400)

        if len(file_bytes) > self.max_file_bytes:
            limit_mb = self.max_file_bytes / (1024 * 1024)
            raise PaddleOCRServiceError(
                f"File exceeds the configured limit of {limit_mb:.0f} MB.",
                status_code=413,
            )

        url = self._build_url("ocr/extract-document")
        files = {
            "file": (
                filename or "document",
                file_bytes,
                content_type or "application/octet-stream",
            )
        }
        response = self._request("POST", url, files=files)
        try:
            return response.json()
        except ValueError as exc:
            raise PaddleOCRServiceError(
                "Invalid JSON response from PaddleOCR-VL"
            ) from exc
