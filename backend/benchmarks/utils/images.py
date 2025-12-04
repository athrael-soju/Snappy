"""
Image processing utilities for benchmarks.
"""

import base64
import logging
from io import BytesIO
from typing import Optional

from PIL import Image

logger = logging.getLogger(__name__)


def encode_image_base64(image: Image.Image, format: str = "PNG") -> str:
    """
    Encode a PIL Image to base64 string.

    Args:
        image: PIL Image to encode
        format: Image format (PNG, JPEG, etc.)

    Returns:
        Base64-encoded string
    """
    buffer = BytesIO()
    image.save(buffer, format=format)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def decode_base64_image(b64_string: str) -> Optional[Image.Image]:
    """
    Decode a base64 string to PIL Image.

    Args:
        b64_string: Base64-encoded image data

    Returns:
        PIL Image or None if decoding fails
    """
    try:
        image_data = base64.b64decode(b64_string)
        return Image.open(BytesIO(image_data)).convert("RGB")
    except Exception as e:
        logger.warning(f"Failed to decode base64 image: {e}")
        return None


def image_to_bytes(image: Image.Image, format: str = "PNG") -> bytes:
    """
    Convert a PIL Image to bytes.

    Args:
        image: PIL Image to convert
        format: Image format (PNG, JPEG, etc.)

    Returns:
        Image bytes
    """
    buffer = BytesIO()
    image.save(buffer, format=format)
    return buffer.getvalue()
