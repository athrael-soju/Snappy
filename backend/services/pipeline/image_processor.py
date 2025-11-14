"""Centralized image processing service.

This module provides a single point for image format conversion and quality
optimization, eliminating redundant conversions across MinIO and OCR services.
"""

import io
import logging
from typing import Dict, Optional

from PIL import Image

logger = logging.getLogger(__name__)


class ProcessedImage:
    """Container for processed image data with metadata."""

    def __init__(
        self,
        data: bytes,
        format: str,
        content_type: str,
        size: int,
        width: int | None = None,
        height: int | None = None,
    ):
        """
        Initialize processed image container.

        Parameters
        ----------
        data : bytes
            Encoded image data
        format : str
            Image format (PNG, JPEG, WEBP)
        content_type : str
            MIME content type
        size : int
            Size in bytes
        width : int | None
            Image width in pixels
        height : int | None
            Image height in pixels
        """
        self.data = data
        self.format = format
        self.content_type = content_type
        self.size = size
        self.width = width
        self.height = height
        self.url: str | None = None  # Set by storage handler

    def to_buffer(self) -> io.BytesIO:
        """Create a BytesIO buffer from the processed data."""
        buf = io.BytesIO(self.data)
        buf.seek(0)
        return buf


class ImageProcessor:
    """
    Centralized image processing service.

    Handles format conversion and quality optimization for images before
    they are passed to storage (MinIO) or OCR (DeepSeek) services.

    This eliminates redundant image conversions and ensures consistent
    processing across all services.
    """

    # Content type mapping
    CONTENT_TYPES: Dict[str, str] = {
        "PNG": "image/png",
        "JPEG": "image/jpeg",
        "JPG": "image/jpeg",
        "WEBP": "image/webp",
    }

    def __init__(
        self,
        default_format: str = "JPEG",
        default_quality: int = 75,
    ):
        """
        Initialize the image processor.

        Parameters
        ----------
        default_format : str
            Default image format (PNG, JPEG, WEBP)
        default_quality : int
            Default compression quality for lossy formats (1-100)
        """
        self.default_format = default_format.upper()
        self.default_quality = max(1, min(100, default_quality))

        # Validate format
        if self.default_format not in self.CONTENT_TYPES:
            logger.warning(
                f"Invalid default format '{default_format}', falling back to JPEG"
            )
            self.default_format = "JPEG"

        logger.info(
            f"ImageProcessor initialized: format={self.default_format}, "
            f"quality={self.default_quality}"
        )

    def process(
        self,
        image: Image.Image,
        *,
        format: Optional[str] = None,
        quality: Optional[int] = None,
        **save_kwargs,
    ) -> ProcessedImage:
        """
        Process a PIL image into the configured format with quality settings.

        This method performs the image conversion once, and the result can be
        reused by multiple consumers (MinIO, OCR, etc.).

        Parameters
        ----------
        image : Image.Image
            PIL Image to process
        format : str, optional
            Output format (PNG, JPEG, WEBP). Uses default if not specified.
        quality : int, optional
            Compression quality (1-100) for lossy formats. Uses default if not specified.
        **save_kwargs
            Additional PIL save parameters (e.g., optimize=True)

        Returns
        -------
        ProcessedImage
            Container with encoded image data and metadata

        Examples
        --------
        >>> processor = ImageProcessor(default_format="JPEG", default_quality=85)
        >>> processed = processor.process(pil_image)
        >>> # Reuse for MinIO
        >>> minio.store_from_bytes(processed.data, ...)
        >>> # Reuse for OCR
        >>> ocr.run_ocr_bytes(processed.data, ...)
        """
        # Use defaults if not specified
        output_format = (format or self.default_format).upper()
        output_quality = quality if quality is not None else self.default_quality

        # Validate format
        if output_format not in self.CONTENT_TYPES:
            logger.warning(
                f"Invalid format '{output_format}', using default {self.default_format}"
            )
            output_format = self.default_format

        # Build save kwargs with quality (for lossy formats)
        final_save_kwargs = dict(save_kwargs)
        if output_format in ("JPEG", "WEBP"):
            final_save_kwargs.setdefault("quality", output_quality)

        # Handle RGBA -> RGB conversion for JPEG
        if output_format == "JPEG" and image.mode in ("RGBA", "LA", "P"):
            # Convert to RGB (JPEG doesn't support transparency)
            rgb_image = Image.new("RGB", image.size, (255, 255, 255))
            if image.mode == "P":
                image = image.convert("RGBA")
            rgb_image.paste(
                image, mask=image.split()[-1] if image.mode in ("RGBA", "LA") else None
            )
            image = rgb_image

        # Encode image to bytes
        buffer = io.BytesIO()
        image.save(buffer, format=output_format, **final_save_kwargs)
        data = buffer.getvalue()
        size = len(data)

        content_type = self.CONTENT_TYPES.get(output_format, "application/octet-stream")

        # Capture image dimensions
        width, height = image.size

        logger.debug(
            f"Processed image: format={output_format}, size={size} bytes, "
            f"dimensions={width}x{height}, "
            f"quality={output_quality if output_format in ('JPEG', 'WEBP') else 'N/A'}"
        )

        return ProcessedImage(
            data=data,
            format=output_format,
            content_type=content_type,
            size=size,
            width=width,
            height=height,
        )

    def process_batch(
        self,
        images: list[Image.Image],
        *,
        format: Optional[str] = None,
        quality: Optional[int] = None,
        **save_kwargs,
    ) -> list[ProcessedImage]:
        """
        Process a batch of images with the same settings.

        Parameters
        ----------
        images : list[Image.Image]
            List of PIL Images to process
        format : str, optional
            Output format for all images
        quality : int, optional
            Compression quality for all images
        **save_kwargs
            Additional PIL save parameters

        Returns
        -------
        list[ProcessedImage]
            List of processed image containers
        """
        return [
            self.process(img, format=format, quality=quality, **save_kwargs)
            for img in images
        ]

    def get_extension(self, format: Optional[str] = None) -> str:
        """
        Get the file extension for the given format.

        Parameters
        ----------
        format : str, optional
            Image format. Uses default if not specified.

        Returns
        -------
        str
            Lowercase file extension (e.g., 'jpg', 'png', 'webp')
        """
        fmt = (format or self.default_format).upper()
        extension_map = {
            "JPEG": "jpg",
            "PNG": "png",
            "WEBP": "webp",
        }
        return extension_map.get(fmt, "jpg")

    def get_content_type(self, format: Optional[str] = None) -> str:
        """
        Get the MIME content type for the given format.

        Parameters
        ----------
        format : str, optional
            Image format. Uses default if not specified.

        Returns
        -------
        str
            MIME content type (e.g., 'image/jpeg')
        """
        fmt = (format or self.default_format).upper()
        return self.CONTENT_TYPES.get(fmt, "application/octet-stream")
