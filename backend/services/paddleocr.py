import base64
import io
import logging
from pathlib import Path
from typing import IO, Any, Dict, Iterable, List, Mapping, Optional, Sequence, Union

import requests
from config import PADDLEOCR_API_TIMEOUT, PADDLEOCR_URL
from PIL import Image
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

UploadedContent = Union[bytes, Image.Image, Path, str, IO[bytes]]


class PaddleOCRService:
    """Client for the PaddleOCR-VL layout parsing API."""

    DEFAULT_ENDPOINT = "/layout-parsing"

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: Optional[int] = None,
        endpoint: Optional[str] = None,
    ) -> None:
        default_base = (PADDLEOCR_URL or "http://localhost:8118").rstrip("/")
        self.base_url = (base_url or default_base).rstrip("/")
        self.timeout = timeout or PADDLEOCR_API_TIMEOUT
        self.endpoint = endpoint or self.DEFAULT_ENDPOINT

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

        self._logger = logging.getLogger(__name__)

    def _read_bytes(self, content: UploadedContent) -> bytes:
        """Normalise supported input types to raw bytes."""
        if isinstance(content, bytes):
            return content

        if isinstance(content, Image.Image):
            buffer = io.BytesIO()
            # Preserve original format when possible while ensuring compatibility.
            format_hint = content.format or "PNG"
            content.save(buffer, format=format_hint)
            buffer.seek(0)
            return buffer.read()

        if isinstance(content, (str, Path)):
            return Path(content).expanduser().resolve().read_bytes()

        if hasattr(content, "read"):
            raw = content.read()
            if isinstance(raw, str):  # pragma: no cover - defensive
                return raw.encode("utf-8")
            return raw

        raise TypeError(
            f"Unsupported content type '{type(content).__name__}' for PaddleOCR payload"
        )

    def _encode_payload(
        self,
        content: UploadedContent,
        file_type: int = 1,
        extra_options: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create the JSON payload expected by PaddleOCR."""
        payload: Dict[str, Any] = {
            "file": base64.b64encode(self._read_bytes(content)).decode("utf-8"),
            "fileType": file_type,
        }
        if extra_options:
            payload.update(extra_options)
        return payload

    def health_check(self) -> bool:
        """Best-effort health check for the PaddleOCR service."""
        candidates = ("healthz", "health", "", "openapi.json")
        for suffix in candidates:
            try:
                url = f"{self.base_url}/{suffix}".rstrip("/")
                response = self.session.get(url, timeout=min(10, self.timeout))
                if response.ok:
                    return True
            except Exception as exc:  # pragma: no cover - defensive guard
                self._logger.debug("Health check %s failed: %s", suffix, exc)
                continue
        return False

    def layout_parsing(
        self,
        content: UploadedContent,
        *,
        file_type: int = 1,
        options: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Call the PaddleOCR layout parsing endpoint with the provided content.

        Args:
            content: Image bytes, PIL image, file path, or file-like object.
            file_type: Media type flag recognised by PaddleOCR (defaults to image=1).
            options: Additional JSON fields to include in the request payload.

        Returns:
            Parsed JSON response from the PaddleOCR service.
        """
        payload = self._encode_payload(
            content, file_type=file_type, extra_options=options
        )
        url = f"{self.base_url}{self.endpoint}"
        try:
            response = self.session.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
        except requests.HTTPError as exc:
            detail = exc.response.text if exc.response is not None else str(exc)
            message = f"PaddleOCR request failed with status {exc.response.status_code if exc.response else 'unknown'}: {detail}"
            self._logger.error(message)
            raise RuntimeError(message) from exc
        except Exception as exc:
            self._logger.error("PaddleOCR request to %s failed: %s", url, exc)
            raise

        try:
            return response.json()
        except ValueError as exc:
            self._logger.error("Invalid JSON payload from PaddleOCR: %s", exc)
            raise RuntimeError("PaddleOCR returned a non-JSON response") from exc

    def extract_text(
        self,
        response_payload: Mapping[str, Any],
    ) -> List[str]:
        """
        Extract recognised text segments from the layout parsing response.

        The PaddleOCR payload nests text inside ``result.layoutParsingResults[*].prunedResult``.
        This helper flattens that structure to make the recognised text easier to consume.
        """
        results = (
            response_payload.get("result", {})
            if isinstance(response_payload, Mapping)
            else {}
        )
        layout_items: Iterable[Mapping[str, Any]] = results.get(
            "layoutParsingResults", []
        )

        collected: List[str] = []
        for item in layout_items:
            pruned: Sequence[Mapping[str, Any]] = item.get("prunedResult", [])  # type: ignore[assignment]
            for block in pruned or []:
                if not isinstance(block, Mapping):
                    continue
                text_candidates: Iterable[str] = []
                if "text" in block:
                    text_candidates = [block["text"]]
                elif "ocrResult" in block and isinstance(block["ocrResult"], Mapping):
                    text_candidates = [
                        line.get("text", "")
                        for line in block["ocrResult"].get("result", [])
                        if isinstance(line, Mapping)
                    ]
                elif "res" in block and isinstance(block["res"], Mapping):
                    maybe_text = block["res"].get("text")
                    if maybe_text:
                        text_candidates = [maybe_text]

                for candidate in text_candidates:
                    if isinstance(candidate, str) and candidate.strip():
                        collected.append(candidate.strip())

        return collected
