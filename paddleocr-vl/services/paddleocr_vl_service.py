"""
PaddleOCR-VL service wrapper for document OCR processing.
"""

import json
import os
import tempfile
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from config.logging_config import get_logger
from config.settings import settings

logger = get_logger(__name__)


class PaddleOCRVLService:
    """
    Thread-safe wrapper for the PaddleOCR-VL pipeline.
    Eagerly initializes the OCR pipeline during service startup.
    """

    _instance: Optional["PaddleOCRVLService"] = None
    _lock = threading.RLock()
    _pipeline = None
    _initialized = False

    def __new__(cls):
        """Singleton pattern to ensure only one instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the service and eagerly load the pipeline."""
        if not self._initialized:
            with self._lock:
                if not self._initialized:
                    logger.info("PaddleOCRVLService initializing pipeline at startup")
                    self._initialize_pipeline()
                    self._initialized = True

    def _initialize_pipeline(self) -> None:
        """
        Initialize the PaddleOCR-VL pipeline.
        Primarily invoked during startup, but safe to call multiple times.
        """
        if self._pipeline is not None:
            return

        with self._lock:
            if self._pipeline is not None:
                return

            logger.info("Initializing PaddleOCR-VL pipeline...")
            start_time = time.time()

            try:
                from paddleocr import PaddleOCRVL

                # Initialize pipeline (GPU usage is automatic based on CUDA availability)
                self._pipeline = PaddleOCRVL()

                elapsed = time.time() - start_time
                logger.info(
                    f"PaddleOCR-VL pipeline initialized successfully in {elapsed:.2f}s"
                )
                logger.info(f"GPU support: {settings.use_gpu}")

            except Exception as e:
                logger.error(f"Failed to initialize PaddleOCR-VL pipeline: {e}")
                raise RuntimeError(f"PaddleOCR-VL initialization failed: {e}") from e

    def process_image(self, image_path: str) -> List[Dict[str, Any]]:
        """
        Process an image file and extract document structure.

        Args:
            image_path: Path to the image file

        Returns:
            List of OCR results with document structure

        Raises:
            RuntimeError: If pipeline initialization or processing fails
        """
        # Safety guard in case startup initialization did not complete
        if self._pipeline is None:
            self._initialize_pipeline()

        try:
            start_time = time.time()
            logger.info(f"Processing image: {image_path}")

            # Run PaddleOCR-VL prediction
            output = self._pipeline.predict(image_path)

            # Convert results using the library-provided serializer
            results = [self._result_to_dict(res) for res in output]

            elapsed = time.time() - start_time
            logger.info(
                f"Image processed successfully in {elapsed:.2f}s - Found {len(results)} results"
            )

            return results

        except Exception as e:
            logger.error(f"Error processing image: {e}")
            raise RuntimeError(f"Image processing failed: {e}") from e

    def process_image_bytes(
        self, image_bytes: bytes, filename: str = "image.jpg"
    ) -> List[Dict[str, Any]]:
        """
        Process image from bytes.

        Args:
            image_bytes: Image file bytes
            filename: Original filename (for extension detection)

        Returns:
            List of OCR results with document structure

        Raises:
            RuntimeError: If processing fails
        """
        # Create temporary file
        suffix = Path(filename).suffix or ".jpg"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temp_file:
            temp_file.write(image_bytes)
            temp_path = temp_file.name

        try:
            # Process the temporary file
            results = self.process_image(temp_path)
            return results
        finally:
            # Clean up temporary file
            try:
                Path(temp_path).unlink()
            except Exception as e:
                logger.warning(f"Failed to delete temporary file {temp_path}: {e}")

    def _result_to_dict(self, result: Any) -> Dict[str, Any]:
        """
        Convert a PaddleOCR-VL result object into a JSON-compatible dictionary
        using the library's native serializer.
        """
        if hasattr(result, "save_to_json") and callable(result.save_to_json):
            temp_path: Optional[Path] = None
            try:
                json_payload = result.save_to_json()

                # Direct dict/list response
                if isinstance(json_payload, (dict, list)):
                    return json_payload  # type: ignore[return-value]

                # JSON string response
                if isinstance(json_payload, bytes):
                    json_payload = json_payload.decode("utf-8")

                if isinstance(json_payload, str):
                    try:
                        return json.loads(json_payload)
                    except json.JSONDecodeError:
                        temp_candidate = Path(json_payload)
                        if temp_candidate.exists():
                            return json.loads(
                                temp_candidate.read_text(encoding="utf-8")
                            )

                # If the method requires a path argument, retry with a temp file
                fd, temp_name = tempfile.mkstemp(suffix=".json")
                os.close(fd)
                temp_path = Path(temp_name)
                result.save_to_json(str(temp_path))
                return json.loads(temp_path.read_text(encoding="utf-8"))
            except TypeError:
                # Method likely requires an explicit path argument
                fd, temp_name = tempfile.mkstemp(suffix=".json")
                os.close(fd)
                temp_path = Path(temp_name)
                try:
                    result.save_to_json(str(temp_path))
                    return json.loads(temp_path.read_text(encoding="utf-8"))
                finally:
                    if temp_path.exists():
                        temp_path.unlink(missing_ok=True)
            except Exception as exc:
                logger.warning(
                    "Failed to serialize PaddleOCR-VL result via save_to_json: %s", exc
                )
            finally:
                if temp_path and temp_path.exists():
                    temp_path.unlink(missing_ok=True)

        logger.warning("Falling back to string representation for OCR result")
        return {"raw": str(result)}

    def is_ready(self) -> bool:
        """Check if the pipeline is initialized and ready."""
        return self._pipeline is not None

    def get_status(self) -> Dict[str, Any]:
        """Get service status information."""
        return {
            "initialized": self.is_ready(),
            "gpu_enabled": settings.use_gpu,
            "device": settings.device,
        }


# Global service instance
paddleocr_vl_service = PaddleOCRVLService()
