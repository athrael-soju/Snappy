"""Main OCR service that orchestrates all operations."""

from __future__ import annotations

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
    from clients.duckdb import DuckDBService
    from clients.minio import MinioService

from .processor import OcrProcessor
from .storage import OcrStorageHandler

logger = logging.getLogger(__name__)


class OcrService:
    """Main service class for OCR operations."""

    def __init__(
        self,
        minio_service: Optional["MinioService"] = None,
        duckdb_service: Optional["DuckDBService"] = None,
        base_url: Optional[str] = None,
        timeout: Optional[int] = None,
        enabled: Optional[bool] = None,
        pool_size: Optional[int] = None,
        default_mode: Optional[str] = None,
        default_task: Optional[str] = None,
        include_grounding: Optional[bool] = None,
        include_images: Optional[bool] = None,
    ):
        """Initialize OCR service with all subcomponents.

        Args:
            minio_service: MinIO service for image storage
            duckdb_service: DuckDB service for analytics storage
            base_url: DeepSeek OCR service URL
            timeout: Request timeout in seconds
            enabled: Enable/disable OCR service
            pool_size: HTTP connection pool size
            default_mode: Default OCR processing mode
            default_task: Default OCR task type
            include_grounding: Default grounding inclusion
            include_images: Default image extraction
        """
        try:
            if minio_service is None:
                raise ValueError("MinIO service is required for OcrService")

            # Initialize HTTP client for DeepSeek OCR
            self.enabled = (
                enabled if enabled is not None else bool(config.DEEPSEEK_OCR_ENABLED)
            )
            default_base = config.DEEPSEEK_OCR_URL or "http://localhost:8200"
            self.base_url = (base_url or default_base).rstrip("/")
            self.timeout = timeout or int(config.DEEPSEEK_OCR_API_TIMEOUT)

            # Get configuration values with fallbacks
            if pool_size is None:
                pool_size = getattr(config, "DEEPSEEK_OCR_POOL_SIZE", 20)
            pool_size = max(5, min(100, int(pool_size or 20)))

            # Default processing options
            self.default_mode = default_mode or getattr(
                config, "DEEPSEEK_OCR_MODE", "Gundam"
            )
            self.default_task = default_task or getattr(
                config, "DEEPSEEK_OCR_TASK", "markdown"
            )
            self.default_locate_text = getattr(config, "DEEPSEEK_OCR_LOCATE_TEXT", "")
            self.default_custom_prompt = getattr(
                config, "DEEPSEEK_OCR_CUSTOM_PROMPT", ""
            )
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
            self.minio_service = minio_service

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

            self.storage = OcrStorageHandler(
                minio_service=minio_service,
                processor=self.processor,
                duckdb_service=duckdb_service,
            )

        except Exception as e:
            raise Exception(f"Failed to initialize OCR service: {e}")

    # HTTP client methods (internal)
    def is_enabled(self) -> bool:
        """Return True when runtime configuration permits OCR usage."""
        return self.enabled

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
        """Execute OCR request against the DeepSeek OCR API."""
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

    # Public orchestration methods
    def process_document_page(
        self,
        filename: str,
        page_number: int,
        *,
        mode: Optional[str] = None,
        task: Optional[str] = None,
        custom_prompt: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Process a single document page with OCR."""
        image_bytes = self._fetch_page_image(filename, page_number)

        ocr_result = self.processor.process_single(
            image_bytes=image_bytes,
            filename=f"{filename}/page_{page_number}.png",
            mode=mode,
            task=task,
            custom_prompt=custom_prompt,
        )

        storage_url = self.storage.store_ocr_result(
            ocr_result=ocr_result,
            filename=filename,
            page_number=page_number,
            metadata=metadata,
        )

        return {
            "status": "success",
            "filename": filename,
            "page_number": page_number,
            "storage_url": storage_url,
            "text_preview": ocr_result.get("text", "")[:200],
            "regions": len(ocr_result.get("regions", [])),
            "extracted_images": len(ocr_result.get("crops", [])),
        }

    def process_document_batch(
        self,
        filename: str,
        page_numbers: List[int],
        *,
        mode: Optional[str] = None,
        task: Optional[str] = None,
        max_workers: Optional[int] = None,
    ) -> List[Optional[Dict[str, Any]]]:
        """Process multiple pages from the same document in parallel."""
        return self.processor.process_batch(
            filename=filename,
            page_numbers=page_numbers,
            minio_service=self.minio_service,
            storage_handler=self.storage,
            mode=mode,
            task=task,
            max_workers=max_workers,
        )

    def fetch_ocr_result(
        self, filename: str, page_number: int
    ) -> Optional[Dict[str, Any]]:
        """Fetch stored OCR result for a page."""
        return self.storage.fetch_ocr_result(filename, page_number)

    def _fetch_page_image(self, filename: str, page_number: int) -> bytes:
        """Fetch page image bytes from MinIO.

        Note: With UUID-based naming, we need to list objects in the image/ subfolder
        to find the page image since we don't have the UUID readily available.
        """
        # List objects in the image/ subfolder for this page
        prefix = f"{filename}/{page_number}/image/"

        for obj in self.minio_service.service.list_objects(
            bucket_name=self.minio_service.bucket_name,
            prefix=prefix,
        ):
            object_name = getattr(obj, "object_name", "")
            if object_name:
                # Found the page image, fetch it
                response = self.minio_service.service.get_object(
                    bucket_name=self.minio_service.bucket_name,
                    object_name=object_name,
                )
                return response.read()

        # No image found
        raise FileNotFoundError(
            f"Page image not found for {filename} page {page_number} in image/ subfolder"
        )

    def health_check(self) -> bool:
        """Check if OCR service is healthy and accessible."""
        if not self.enabled:
            logger.debug("Skipping DeepSeek health check: service disabled")
            return False
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=self.timeout)
            response.raise_for_status()
            payload = response.json()
            return bool(payload.get("status") == "healthy")
        except Exception as exc:
            logger.warning("DeepSeek OCR health check failed: %s", exc)
            return False

    def close(self):
        """Close the HTTP session and release connections."""
        if hasattr(self, "session"):
            self.session.close()

    def __del__(self):
        """Ensure session is closed on garbage collection."""
        self.close()
