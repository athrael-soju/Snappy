import logging
import mimetypes
from dataclasses import dataclass
from typing import Any, Dict, Iterable, Optional

import config
import requests
from requests import Response
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class PaddleOcrServiceError(RuntimeError):
    """Raised when the PaddleOCR-VL service returns an error or is unreachable."""

    def __init__(
        self,
        message: str,
        *,
        status_code: Optional[int] = None,
        payload: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload or {}


@dataclass(frozen=True)
class PaddleOcrUploadConstraints:
    allowed_extensions: set[str]
    allow_any: bool
    max_file_size_bytes: int


class PaddleOcrService:
    """Synchronous client for the PaddleOCR-VL FastAPI service."""

    OCR_ROUTE = "/ocr/extract-document"
    HEALTH_ROUTE = "/health"

    def __init__(
        self,
        *,
        base_url: Optional[str] = None,
        api_prefix: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> None:
        self._logger = logging.getLogger(__name__)

        raw_base = base_url or getattr(config, "PADDLE_OCR_VL_URL", "")
        if not raw_base:
            raise ValueError("PADDLE_OCR_VL_URL must be configured")
        self.base_url = raw_base.rstrip("/")

        self.api_prefix = self._normalise_prefix(
            api_prefix or getattr(config, "PADDLE_OCR_VL_API_PREFIX", "")
        )
        self.timeout = timeout or getattr(config, "PADDLE_OCR_VL_API_TIMEOUT", 300)

        self.health_url = f"{self.base_url}{self.HEALTH_ROUTE}"
        self.ocr_url = f"{self.base_url}{self.api_prefix}{self.OCR_ROUTE}"

        self._constraints = self._load_constraints()

        self.enabled = bool(getattr(config, "PADDLE_OCR_VL_ENABLED", False))

        retry_policy = Retry(
            total=3,
            connect=3,
            read=3,
            status=3,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods={"GET", "POST"},
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry_policy)
        session = requests.Session()
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        self._session = session

    @staticmethod
    def _normalise_prefix(prefix: str) -> str:
        if not prefix:
            return ""
        value = prefix.strip()
        if not value.startswith("/"):
            value = f"/{value}"
        return value.rstrip("/")

    def _load_constraints(self) -> PaddleOcrUploadConstraints:
        raw_extensions = getattr(config, "PADDLE_OCR_VL_ALLOWED_EXTENSIONS", [])
        if isinstance(raw_extensions, str):
            raw_extensions = [raw_extensions]
        normalized = self._normalise_extensions(raw_extensions)

        allow_any = False
        if not normalized:
            allow_any = True

        max_mb = getattr(config, "PADDLE_OCR_VL_MAX_FILE_SIZE_MB", 50)
        try:
            max_mb_value = max(1, int(max_mb))
        except (TypeError, ValueError):
            self._logger.warning(
                "Invalid PADDLE_OCR_VL_MAX_FILE_SIZE_MB value %s; defaulting to 50MB",
                max_mb,
            )
            max_mb_value = 50
        max_file_size_bytes = max_mb_value * 1024 * 1024

        return PaddleOcrUploadConstraints(
            allowed_extensions=normalized,
            allow_any=allow_any,
            max_file_size_bytes=max_file_size_bytes,
        )

    @staticmethod
    def _normalise_extensions(values: Iterable[str]) -> set[str]:
        normalised: set[str] = set()
        for raw in values:
            if raw is None:
                continue
            value = str(raw).strip().lower()
            if not value:
                continue
            if value == "*":
                return set()
            if not value.startswith("."):
                value = f".{value}"
            normalised.add(value)
        return normalised

    def upload_constraints(self) -> PaddleOcrUploadConstraints:
        return self._constraints

    def is_enabled(self) -> bool:
        return self.enabled

    def _perform_request(self, method: str, url: str, **kwargs: Any) -> Dict[str, Any]:
        try:
            response = self._session.request(
                method, url, timeout=self.timeout, **kwargs
            )
        except requests.RequestException as exc:  # pragma: no cover - network failure
            raise PaddleOcrServiceError(f"PaddleOCR-VL request failed: {exc}") from exc

        if response.status_code >= 400:
            raise self._build_error(response)

        try:
            return response.json()
        except ValueError as exc:
            raise PaddleOcrServiceError(
                "PaddleOCR-VL returned a non-JSON response",
                status_code=response.status_code,
            ) from exc

    def _build_error(self, resp: Response) -> PaddleOcrServiceError:
        payload: Dict[str, Any] | None = None
        message = f"PaddleOCR-VL responded with status {resp.status_code}"
        try:
            payload = resp.json()
        except ValueError:
            payload = None

        if payload:
            detail = payload.get("detail") or payload.get("message")
            if isinstance(detail, str):
                message = detail
            elif isinstance(payload.get("errors"), list):
                message = "; ".join(str(item) for item in payload["errors"])

        return PaddleOcrServiceError(
            message,
            status_code=resp.status_code,
            payload=payload or {"raw": resp.text},
        )

    def extract_document(
        self, file_bytes: bytes, *, filename: str, content_type: Optional[str] = None
    ) -> Dict[str, Any]:
        if not self.enabled:
            raise PaddleOcrServiceError(
                "PaddleOCR-VL integration is disabled.", status_code=503
            )

        mimetype = (
            content_type
            or mimetypes.guess_type(filename)[0]
            or "application/octet-stream"
        )
        files = {"file": (filename, file_bytes, mimetype)}
        return self._perform_request("POST", self.ocr_url, files=files)

    def health(self) -> Dict[str, Any]:
        return self._perform_request("GET", self.health_url)
