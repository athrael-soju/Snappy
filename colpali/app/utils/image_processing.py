"""Image processing utilities."""

from io import BytesIO

from PIL import Image


def load_image_from_bytes(image_bytes: bytes) -> Image.Image:
    """Load PIL Image from bytes.

    Args:
        image_bytes: Raw image bytes

    Returns:
        PIL Image in RGB mode
    """
    return Image.open(BytesIO(image_bytes)).convert("RGB")
