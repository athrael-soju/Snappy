"""
PaddleOCR-VL service wrapper for document OCR processing.
"""

import json
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
    Thread-safe wrapper for PaddleOCR-VL pipeline.
    Implements lazy initialization and manages the OCR pipeline lifecycle.
    """

    _instance: Optional["PaddleOCRVLService"] = None
    _lock = threading.Lock()
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
        """Initialize the service (lazy loading)."""
        if not self._initialized:
            with self._lock:
                if not self._initialized:
                    logger.info(
                        "PaddleOCRVLService instance created (pipeline will be initialized on first use)"
                    )
                    self._initialized = True

    def _make_serializable(self, obj: Any) -> Any:
        """
        Convert any object to JSON-serializable format.
        Handles nested structures, filters out methods, and converts complex types.

        Args:
            obj: Any Python object

        Returns:
            JSON-serializable version of the object
        """
        # Handle None, primitives (str, int, float, bool)
        if obj is None or isinstance(obj, (str, int, float, bool)):
            return obj

        # Handle lists
        if isinstance(obj, (list, tuple)):
            return [self._make_serializable(item) for item in obj]

        # Handle dicts
        if isinstance(obj, dict):
            return {
                k: self._make_serializable(v) for k, v in obj.items() if not callable(v)
            }

        # Skip callables (methods, functions)
        if callable(obj):
            return None

        # Try to convert to dict if it has __dict__
        if hasattr(obj, "__dict__"):
            try:
                return {
                    k: self._make_serializable(v)
                    for k, v in obj.__dict__.items()
                    if not k.startswith("_") and not callable(v)
                }
            except Exception:
                pass

        # Fall back to string representation for unknown types
        try:
            # Test if it's JSON serializable
            json.dumps(obj)
            return obj
        except (TypeError, ValueError):
            return str(obj)

    def _initialize_pipeline(self) -> None:
        """
        Initialize the PaddleOCR-VL pipeline.
        This is called lazily on first use to avoid loading models during startup.
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
        # Ensure pipeline is initialized
        if self._pipeline is None:
            self._initialize_pipeline()

        try:
            start_time = time.time()
            logger.info(f"Processing image: {image_path}")

            # Run PaddleOCR-VL prediction
            output = self._pipeline.predict(image_path)

            # Convert results to dict format
            results = []
            for idx, res in enumerate(output):
                # Extract result data
                result_data = {
                    "index": idx,
                    "content": self._extract_content(res),
                    "metadata": self._extract_metadata(res),
                }
                results.append(result_data)

            elapsed = time.time() - start_time
            logger.info(
                f"Image processed successfully in {elapsed:.2f}s - Found {len(results)} elements"
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

    def _extract_content(self, result: Any) -> Dict[str, Any]:
        """
        Extract content from PaddleOCR-VL result object.

        Args:
            result: PaddleOCR-VL result object

        Returns:
            Dictionary containing extracted text and structure
        """
        try:
            # Convert result to string first (it's a complex object)
            result_str = str(result)

            # Extract parsing_res_list which contains the actual OCR results
            content = {}

            # Parse the string representation to find content blocks
            import re

            # Find all content blocks in the format:
            # label:\ttype\nbbox:\t[coords]\ncontent:\ttext
            pattern = r"label:\s*(\w+)\s*\n\s*bbox:\s*\[([^\]]+)\]\s*\n\s*content:\s*(.+?)(?=\n#####|$)"
            matches = re.findall(pattern, result_str, re.DOTALL)

            if matches:
                blocks = []
                for label, bbox_str, text in matches:
                    # Parse bbox coordinates
                    try:
                        bbox = [
                            float(x.strip().replace("np.float32(", "").replace(")", ""))
                            for x in bbox_str.split(",")[:4]
                        ]
                    except:
                        bbox = []

                    blocks.append(
                        {"type": label.strip(), "bbox": bbox, "text": text.strip()}
                    )

                content["blocks"] = blocks
                # Create a simple text concatenation
                content["text"] = "\n\n".join(block["text"] for block in blocks)

            # Try to call conversion methods if available
            if hasattr(result, "to_markdown") and callable(result.to_markdown):
                try:
                    content["markdown"] = result.to_markdown()
                except Exception as e:
                    logger.debug(f"Failed to call to_markdown(): {e}")

            # If we got some content, return it
            if content:
                return content

            # Fallback: return string representation
            return {"raw": result_str}

        except Exception as e:
            logger.warning(f"Failed to extract content: {e}")
            return {"raw": str(result)}

    def _extract_metadata(self, result: Any) -> Dict[str, Any]:
        """
        Extract metadata from PaddleOCR-VL result object.

        Args:
            result: PaddleOCR-VL result object

        Returns:
            Dictionary containing metadata
        """
        metadata = {}

        # Try to extract common metadata fields
        for attr in ["bbox", "confidence", "type", "label"]:
            if hasattr(result, attr):
                value = getattr(result, attr)
                # Make value serializable
                serialized_value = self._make_serializable(value)
                if serialized_value is not None:
                    metadata[attr] = serialized_value

        return metadata

    def get_markdown_output(self, results: List[Dict[str, Any]]) -> str:
        """
        Convert results to markdown format.

        Args:
            results: List of OCR results

        Returns:
            Markdown formatted string
        """
        markdown_parts = []
        markdown_parts.append("# Document OCR Results\n")

        for idx, result in enumerate(results):
            markdown_parts.append(f"\n## Element {idx + 1}\n")

            content = result.get("content", {})
            if isinstance(content, dict):
                for key, value in content.items():
                    markdown_parts.append(f"**{key}**: {value}\n")
            else:
                markdown_parts.append(f"{content}\n")

        return "\n".join(markdown_parts)

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
