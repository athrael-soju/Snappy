"""
Utility script to extract OCR from document images.

This script processes a directory of images and generates OCR JSON files
compatible with the evaluation suite.
"""

import argparse
import asyncio
import base64
import json
import logging
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiohttp
from PIL import Image

logger = logging.getLogger(__name__)


async def extract_ocr_deepseek(
    image_path: Path,
    ocr_url: str = "http://localhost:8002",
    timeout: float = 60.0,
) -> Dict[str, Any]:
    """
    Extract OCR using DeepSeek OCR service.

    Args:
        image_path: Path to image file
        ocr_url: URL of DeepSeek OCR service
        timeout: Request timeout

    Returns:
        OCR result with regions and full_text
    """
    # Load and encode image
    with Image.open(image_path) as img:
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        image_b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

    async with aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=timeout)
    ) as session:
        async with session.post(
            f"{ocr_url}/ocr",
            json={"image": image_b64, "return_regions": True},
        ) as response:
            response.raise_for_status()
            return await response.json()


def convert_ocr_format(raw_ocr: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert raw OCR response to evaluation format.

    Args:
        raw_ocr: Raw OCR response from service

    Returns:
        Standardized OCR format
    """
    regions = []
    full_text_parts = []

    # Handle different OCR response formats
    raw_regions = raw_ocr.get("regions") or raw_ocr.get("blocks") or []

    for region in raw_regions:
        content = region.get("content") or region.get("text", "")
        bbox = region.get("bbox") or region.get("bounding_box", [])

        if content and bbox:
            # Ensure bbox is [x1, y1, x2, y2] format
            if isinstance(bbox, dict):
                bbox = [
                    bbox.get("x1", bbox.get("x", 0)),
                    bbox.get("y1", bbox.get("y", 0)),
                    bbox.get("x2", bbox.get("x", 0) + bbox.get("width", 0)),
                    bbox.get("y2", bbox.get("y", 0) + bbox.get("height", 0)),
                ]

            regions.append({
                "content": content,
                "bbox": bbox[:4],
                "label": region.get("label", "text"),
                "confidence": region.get("confidence", 1.0),
            })
            full_text_parts.append(content)

    return {
        "regions": regions,
        "full_text": raw_ocr.get("full_text") or "\n".join(full_text_parts),
    }


async def process_directory(
    images_dir: Path,
    output_dir: Path,
    ocr_url: str = "http://localhost:8002",
    extensions: List[str] = [".png", ".jpg", ".jpeg", ".tiff"],
    overwrite: bool = False,
    concurrency: int = 4,
) -> None:
    """
    Process all images in a directory.

    Args:
        images_dir: Directory containing images
        output_dir: Directory to write OCR JSON files
        ocr_url: URL of OCR service
        extensions: Image file extensions to process
        overwrite: Whether to overwrite existing OCR files
        concurrency: Maximum concurrent requests
    """
    images_dir = Path(images_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Find all images
    image_files = []
    for ext in extensions:
        image_files.extend(images_dir.glob(f"*{ext}"))
        image_files.extend(images_dir.glob(f"*{ext.upper()}"))

    logger.info(f"Found {len(image_files)} images to process")

    # Filter out already processed
    if not overwrite:
        to_process = []
        for img_path in image_files:
            ocr_path = output_dir / f"{img_path.stem}.json"
            if not ocr_path.exists():
                to_process.append(img_path)
        image_files = to_process
        logger.info(f"{len(image_files)} images need processing")

    if not image_files:
        logger.info("No images to process")
        return

    # Process with concurrency limit
    semaphore = asyncio.Semaphore(concurrency)
    processed = 0
    failed = 0

    async def process_one(img_path: Path) -> None:
        nonlocal processed, failed
        async with semaphore:
            try:
                logger.info(f"Processing {img_path.name}")
                raw_ocr = await extract_ocr_deepseek(img_path, ocr_url)
                ocr_data = convert_ocr_format(raw_ocr)

                ocr_path = output_dir / f"{img_path.stem}.json"
                with open(ocr_path, "w") as f:
                    json.dump(ocr_data, f, indent=2)

                processed += 1
                logger.info(f"Saved {ocr_path.name} ({len(ocr_data['regions'])} regions)")
            except Exception as e:
                failed += 1
                logger.error(f"Failed to process {img_path.name}: {e}")

    await asyncio.gather(*[process_one(img) for img in image_files])

    logger.info(f"Completed: {processed} processed, {failed} failed")


def main():
    parser = argparse.ArgumentParser(description="Extract OCR from document images")
    parser.add_argument(
        "images_dir",
        type=Path,
        help="Directory containing document images",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory for OCR JSON files (default: images_dir/../ocr)",
    )
    parser.add_argument(
        "--ocr-url",
        type=str,
        default="http://localhost:8002",
        help="DeepSeek OCR service URL",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing OCR files",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=4,
        help="Maximum concurrent OCR requests",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output",
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    output_dir = args.output_dir or args.images_dir.parent / "ocr"

    asyncio.run(
        process_directory(
            args.images_dir,
            output_dir,
            args.ocr_url,
            overwrite=args.overwrite,
            concurrency=args.concurrency,
        )
    )


if __name__ == "__main__":
    main()
