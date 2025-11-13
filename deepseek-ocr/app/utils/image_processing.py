"""
Image processing utilities for bounding boxes and annotations.
"""

import ast
import base64
import re
from io import BytesIO
from typing import List, Tuple

import numpy as np
from app.core.logging import logger
from PIL import Image, ImageDraw, ImageFont


def extract_grounding_references(text: str) -> List[Tuple[str, str, str]]:
    """
    Extract grounding references from model output.

    Args:
        text: Model output containing grounding references

    Returns:
        List of tuples: (full_match, label, coordinates)
    """
    pattern = r"(<\|ref\|>(.*?)<\|/ref\|><\|det\|>(.*?)<\|/det\|>)"
    return re.findall(pattern, text, re.DOTALL)


def draw_bounding_boxes(
    image: Image.Image, refs: List[Tuple[str, str, str]], extract_images: bool = False
) -> Tuple[Image.Image, List[Image.Image]]:
    """
    Draw bounding boxes on image based on grounding references.

    Args:
        image: Input PIL Image
        refs: Grounding references from extract_grounding_references
        extract_images: Whether to extract cropped regions

    Returns:
        Tuple of (annotated_image, list_of_crops)
    """
    img_w, img_h = image.size
    img_draw = image.copy()
    draw = ImageDraw.Draw(img_draw)

    # Create semi-transparent overlay
    overlay = Image.new("RGBA", img_draw.size, (0, 0, 0, 0))
    draw2 = ImageDraw.Draw(overlay)

    # Try to load font, fallback to default if not found
    try:
        font = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 25
        )
    except OSError:
        logger.warning("DejaVu font not found, using default font")
        font = ImageFont.load_default()

    crops = []
    color_map = {}
    np.random.seed(42)

    for ref in refs:
        label = ref[1]

        # Assign consistent color per label
        if label not in color_map:
            color_map[label] = (
                np.random.randint(50, 255),
                np.random.randint(50, 255),
                np.random.randint(50, 255),
            )

        color = color_map[label]
        # Use ast.literal_eval() for safe parsing (prevents code injection)
        try:
            coords = ast.literal_eval(ref[2])
        except (ValueError, SyntaxError) as e:
            logger.error(f"Failed to parse coordinates '{ref[2]}': {e}")
            continue  # Skip this reference if coordinates are malformed
        color_a = color + (60,)  # Semi-transparent version

        for box in coords:
            # Convert normalized coordinates to pixel coordinates
            x1 = int(box[0] / 999 * img_w)
            y1 = int(box[1] / 999 * img_h)
            x2 = int(box[2] / 999 * img_w)
            y2 = int(box[3] / 999 * img_h)

            # Extract image crops if requested
            if extract_images and label == "image":
                crops.append(image.crop((x1, y1, x2, y2)))

            # Draw bounding box
            width = 5 if label == "title" else 3
            draw.rectangle([x1, y1, x2, y2], outline=color, width=width)
            draw2.rectangle([x1, y1, x2, y2], fill=color_a)

            # Draw label
            text_bbox = draw.textbbox((0, 0), label, font=font)
            tw, th = text_bbox[2] - text_bbox[0], text_bbox[3] - text_bbox[1]
            ty = max(0, y1 - 20)
            draw.rectangle([x1, ty, x1 + tw + 4, ty + th + 4], fill=color)
            draw.text((x1 + 2, ty + 2), label, font=font, fill=(255, 255, 255))

    # Composite overlay onto image
    img_draw.paste(overlay, (0, 0), overlay)
    return img_draw, crops


def clean_output(
    text: str, include_images: bool = False, remove_labels: bool = False
) -> str:
    """
    Clean model output by removing/replacing grounding references.

    Args:
        text: Raw model output
        include_images: Whether to keep image placeholders
        remove_labels: Whether to remove all grounding labels

    Returns:
        Cleaned text
    """
    if not text:
        return ""

    pattern = r"(<\|ref\|>(.*?)<\|/ref\|><\|det\|>(.*?)<\|/det\|>)"
    matches = re.findall(pattern, text, re.DOTALL)
    img_num = 0

    for match in matches:
        if "<|ref|>image<|/ref|>" in match[0]:
            if include_images:
                text = text.replace(match[0], f"\n\n**[Figure {img_num + 1}]**\n\n", 1)
                img_num += 1
            else:
                text = text.replace(match[0], "", 1)
        else:
            if remove_labels:
                text = text.replace(match[0], "", 1)
            else:
                text = text.replace(match[0], match[1], 1)

    return text.strip()


def embed_images(markdown: str, crops: List[Image.Image]) -> str:
    """
    Embed base64-encoded images into markdown.

    Args:
        markdown: Markdown text with Figure placeholders
        crops: List of PIL Images to embed

    Returns:
        Markdown with embedded base64 images
    """
    if not crops:
        return markdown

    for i, img in enumerate(crops):
        buf = BytesIO()
        img.save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode()
        markdown = markdown.replace(
            f"**[Figure {i + 1}]**",
            f"\n\n![Figure {i + 1}](data:image/png;base64,{b64})\n\n",
            1,
        )

    return markdown


def image_to_base64(image: Image.Image, format: str = "PNG") -> str:
    """Convert PIL Image to base64 string."""
    buf = BytesIO()
    image.save(buf, format=format)
    return base64.b64encode(buf.getvalue()).decode()
