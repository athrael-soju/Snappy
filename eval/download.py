"""
Dataset download utilities for evaluation.

Supports downloading:
- BBox-DocVQA (when publicly available)
- Standard DocVQA (as fallback/alternative)
- Custom datasets from various sources
"""

import hashlib
import json
import logging
import os
import shutil
import zipfile
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from urllib.parse import urlparse

import requests
from tqdm import tqdm

logger = logging.getLogger(__name__)

# Dataset registry with download configurations
DATASET_REGISTRY: Dict[str, Dict[str, Any]] = {
    "bbox-docvqa": {
        "description": "BBox-DocVQA: Bounding box grounded DocVQA dataset",
        "source": "huggingface",
        "hf_repo": "bbox-docvqa/bbox-docvqa",  # Placeholder - update when released
        "fallback_url": None,
        "expected_files": ["annotations.json", "images/"],
        "status": "pending_release",  # Will be updated when available
    },
    "docvqa": {
        "description": "Standard DocVQA dataset from RRC",
        "source": "huggingface",
        "hf_repo": "lmms-lab/DocVQA",
        "subset": "DocVQA",
        "expected_files": ["train.json", "val.json", "test.json"],
        "status": "available",
    },
    "docvqa-val": {
        "description": "DocVQA validation split only (smaller)",
        "source": "huggingface",
        "hf_repo": "eliolio/docvqa",
        "split": "validation",
        "expected_files": ["data/"],
        "status": "available",
    },
}


class DownloadError(Exception):
    """Raised when download fails."""
    pass


def get_cache_dir() -> Path:
    """Get the cache directory for downloads."""
    cache_dir = Path(os.environ.get("SNAPPY_CACHE_DIR", Path.home() / ".cache" / "snappy"))
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def download_file(
    url: str,
    dest_path: Path,
    chunk_size: int = 8192,
    show_progress: bool = True,
) -> Path:
    """
    Download a file with progress bar.

    Args:
        url: URL to download
        dest_path: Destination path
        chunk_size: Download chunk size
        show_progress: Whether to show progress bar

    Returns:
        Path to downloaded file
    """
    dest_path = Path(dest_path)
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    response = requests.get(url, stream=True)
    response.raise_for_status()

    total_size = int(response.headers.get("content-length", 0))

    with open(dest_path, "wb") as f:
        if show_progress and total_size > 0:
            pbar = tqdm(total=total_size, unit="B", unit_scale=True, desc=dest_path.name)
            for chunk in response.iter_content(chunk_size=chunk_size):
                f.write(chunk)
                pbar.update(len(chunk))
            pbar.close()
        else:
            for chunk in response.iter_content(chunk_size=chunk_size):
                f.write(chunk)

    return dest_path


def download_from_huggingface(
    repo_id: str,
    output_dir: Path,
    subset: Optional[str] = None,
    split: Optional[str] = None,
    token: Optional[str] = None,
) -> Path:
    """
    Download dataset from Hugging Face Hub.

    Args:
        repo_id: Hugging Face repository ID (e.g., "lmms-lab/DocVQA")
        output_dir: Directory to save dataset
        subset: Dataset subset/configuration name
        split: Specific split to download (train, val, test)
        token: Hugging Face API token (for gated datasets)

    Returns:
        Path to downloaded dataset
    """
    try:
        from datasets import load_dataset
    except ImportError:
        raise ImportError(
            "Please install the 'datasets' package: pip install datasets"
        )

    logger.info(f"Downloading {repo_id} from Hugging Face...")

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load dataset
    kwargs = {}
    if subset:
        kwargs["name"] = subset
    if split:
        kwargs["split"] = split
    if token:
        kwargs["token"] = token

    try:
        dataset = load_dataset(repo_id, **kwargs)
    except Exception as e:
        raise DownloadError(f"Failed to download from Hugging Face: {e}")

    # Save to disk
    if split:
        # Single split
        dataset.save_to_disk(output_dir / split)
    else:
        # All splits
        dataset.save_to_disk(output_dir)

    logger.info(f"Dataset saved to {output_dir}")
    return output_dir


def convert_hf_to_eval_format(
    hf_dir: Path,
    output_dir: Path,
    dataset_type: str = "docvqa",
) -> Path:
    """
    Convert Hugging Face dataset format to evaluation format.

    Args:
        hf_dir: Directory with HF dataset
        output_dir: Output directory for converted dataset
        dataset_type: Type of dataset for format conversion

    Returns:
        Path to converted dataset
    """
    try:
        from datasets import load_from_disk
    except ImportError:
        raise ImportError("Please install the 'datasets' package")

    output_dir = Path(output_dir)
    images_dir = output_dir / "images"
    ocr_dir = output_dir / "ocr"
    images_dir.mkdir(parents=True, exist_ok=True)
    ocr_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Converting dataset from {hf_dir} to eval format...")

    dataset = load_from_disk(hf_dir)

    # Handle different dataset structures
    if hasattr(dataset, "keys"):
        # Multiple splits
        splits = list(dataset.keys())
        all_samples = []
        for split_name in splits:
            split_data = dataset[split_name]
            samples = _convert_split(split_data, images_dir, ocr_dir, split_name)
            all_samples.extend(samples)
    else:
        # Single split
        all_samples = _convert_split(dataset, images_dir, ocr_dir, "data")

    # Save annotations
    annotations_path = output_dir / "annotations.json"
    with open(annotations_path, "w") as f:
        json.dump({"samples": all_samples}, f, indent=2)

    logger.info(f"Converted {len(all_samples)} samples to {output_dir}")
    return output_dir


def _convert_split(
    split_data,
    images_dir: Path,
    ocr_dir: Path,
    split_name: str,
) -> List[Dict[str, Any]]:
    """Convert a single dataset split."""
    samples = []

    for idx, item in enumerate(tqdm(split_data, desc=f"Converting {split_name}")):
        sample_id = item.get("questionId") or item.get("question_id") or f"{split_name}_{idx}"

        # Extract image
        image = item.get("image")
        if image is not None:
            image_name = f"{sample_id}.png"
            image_path = images_dir / image_name
            if not image_path.exists():
                image.save(image_path)
        else:
            image_name = item.get("image_name", f"{sample_id}.png")

        # Extract question and answer
        question = item.get("question", "")
        answers = item.get("answers", [])
        answer = answers[0] if answers else item.get("answer", "")

        # Extract bounding box if available
        bbox = None
        if "bbox" in item:
            bbox = item["bbox"]
        elif "bounding_box" in item:
            bbox = item["bounding_box"]
        elif "evidence_bbox" in item:
            bbox = item["evidence_bbox"]

        # Create sample entry
        sample = {
            "sample_id": str(sample_id),
            "image": image_name,
            "question": question,
            "answer": answer,
            "split": split_name,
        }

        if bbox:
            sample["bbox"] = bbox

        # Extract OCR if available
        if "ocr" in item or "words" in item:
            ocr_data = _extract_ocr_from_item(item)
            if ocr_data:
                ocr_path = ocr_dir / f"{sample_id}.json"
                with open(ocr_path, "w") as f:
                    json.dump(ocr_data, f)

        samples.append(sample)

    return samples


def _extract_ocr_from_item(item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Extract OCR data from dataset item."""
    regions = []
    full_text_parts = []

    # Handle different OCR formats
    if "words" in item and "boxes" in item:
        words = item["words"]
        boxes = item["boxes"]
        for word, box in zip(words, boxes):
            if word and box:
                regions.append({
                    "content": word,
                    "bbox": box,
                    "label": "word",
                })
                full_text_parts.append(word)

    elif "ocr" in item:
        ocr = item["ocr"]
        if isinstance(ocr, dict):
            return ocr
        elif isinstance(ocr, str):
            return {"full_text": ocr, "regions": []}

    if not regions and not full_text_parts:
        return None

    return {
        "regions": regions,
        "full_text": " ".join(full_text_parts),
    }


def check_dataset_exists(dataset_dir: Path) -> bool:
    """Check if dataset already exists and is valid."""
    dataset_dir = Path(dataset_dir)

    if not dataset_dir.exists():
        return False

    # Check for required files
    annotations = dataset_dir / "annotations.json"
    images = dataset_dir / "images"

    return annotations.exists() and images.exists() and any(images.iterdir())


def download_dataset(
    dataset_name: str = "bbox-docvqa",
    output_dir: Optional[Path] = None,
    force: bool = False,
    hf_token: Optional[str] = None,
) -> Path:
    """
    Download and prepare a dataset for evaluation.

    Args:
        dataset_name: Name of dataset to download
        output_dir: Output directory (default: data/{dataset_name})
        force: Force re-download even if exists
        hf_token: Hugging Face token for gated datasets

    Returns:
        Path to prepared dataset
    """
    if dataset_name not in DATASET_REGISTRY:
        available = ", ".join(DATASET_REGISTRY.keys())
        raise ValueError(f"Unknown dataset: {dataset_name}. Available: {available}")

    config = DATASET_REGISTRY[dataset_name]

    # Check status
    if config.get("status") == "pending_release":
        logger.warning(
            f"Dataset '{dataset_name}' is not yet publicly available. "
            f"Using alternative dataset or provide custom data."
        )
        # Offer alternatives
        if dataset_name == "bbox-docvqa":
            logger.info("Falling back to standard DocVQA dataset...")
            return download_dataset("docvqa-val", output_dir, force, hf_token)

    # Set output directory
    if output_dir is None:
        output_dir = Path("data") / dataset_name
    else:
        output_dir = Path(output_dir)

    # Check if already exists
    if not force and check_dataset_exists(output_dir):
        logger.info(f"Dataset already exists at {output_dir}")
        return output_dir

    logger.info(f"Downloading {dataset_name}: {config['description']}")

    # Download based on source
    cache_dir = get_cache_dir() / dataset_name

    if config["source"] == "huggingface":
        hf_dir = download_from_huggingface(
            repo_id=config["hf_repo"],
            output_dir=cache_dir,
            subset=config.get("subset"),
            split=config.get("split"),
            token=hf_token,
        )
        # Convert to eval format
        convert_hf_to_eval_format(hf_dir, output_dir, dataset_name)

    elif config["source"] == "url":
        # Direct URL download
        url = config["url"]
        archive_path = cache_dir / "dataset.zip"
        download_file(url, archive_path)

        # Extract
        with zipfile.ZipFile(archive_path, "r") as zf:
            zf.extractall(output_dir)

    logger.info(f"Dataset ready at {output_dir}")
    return output_dir


def create_synthetic_dataset(
    output_dir: Path,
    n_samples: int = 100,
    image_size: tuple = (800, 1000),
) -> Path:
    """
    Create a synthetic dataset for testing the evaluation pipeline.

    This generates random document-like images with text regions and
    synthetic questions/answers. Useful for testing without real data.

    Args:
        output_dir: Output directory
        n_samples: Number of samples to generate
        image_size: Size of generated images (width, height)

    Returns:
        Path to synthetic dataset
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        raise ImportError("Pillow required for synthetic data generation")

    import random
    import string

    output_dir = Path(output_dir)
    images_dir = output_dir / "images"
    ocr_dir = output_dir / "ocr"
    images_dir.mkdir(parents=True, exist_ok=True)
    ocr_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Creating synthetic dataset with {n_samples} samples...")

    samples = []
    random.seed(42)

    # Sample text content
    words = ["invoice", "total", "amount", "date", "customer", "order", "payment",
             "receipt", "tax", "subtotal", "quantity", "price", "item", "service"]
    numbers = ["$123.45", "$567.89", "$1,234.00", "12/25/2024", "#12345"]

    for i in tqdm(range(n_samples), desc="Generating samples"):
        sample_id = f"synthetic_{i:05d}"

        # Create image with white background
        img = Image.new("RGB", image_size, color="white")
        draw = ImageDraw.Draw(img)

        # Generate random text regions
        regions = []
        n_regions = random.randint(5, 15)

        for j in range(n_regions):
            # Random position
            x1 = random.randint(50, image_size[0] - 200)
            y1 = random.randint(50, image_size[1] - 50)

            # Random content
            if random.random() < 0.3:
                content = random.choice(numbers)
            else:
                content = " ".join(random.choices(words, k=random.randint(1, 4)))

            # Draw text
            draw.text((x1, y1), content, fill="black")

            # Estimate bounding box (rough)
            text_width = len(content) * 8
            text_height = 16
            x2 = x1 + text_width
            y2 = y1 + text_height

            regions.append({
                "content": content,
                "bbox": [x1, y1, x2, y2],
                "label": "text",
            })

        # Save image
        image_name = f"{sample_id}.png"
        img.save(images_dir / image_name)

        # Generate question about a random region
        target_region = random.choice(regions)
        question_templates = [
            f"What is the {random.choice(words)}?",
            f"Find the {target_region['content'].split()[0]} value.",
            "What amount is shown?",
        ]
        question = random.choice(question_templates)
        answer = target_region["content"]

        # Save OCR
        ocr_data = {
            "regions": regions,
            "full_text": " ".join(r["content"] for r in regions),
        }
        with open(ocr_dir / f"{sample_id}.json", "w") as f:
            json.dump(ocr_data, f)

        samples.append({
            "sample_id": sample_id,
            "image": image_name,
            "question": question,
            "answer": answer,
            "bbox": target_region["bbox"],
        })

    # Save annotations
    with open(output_dir / "annotations.json", "w") as f:
        json.dump({"samples": samples}, f, indent=2)

    logger.info(f"Created synthetic dataset at {output_dir}")
    return output_dir


def list_available_datasets() -> Dict[str, str]:
    """List all available datasets with their status."""
    return {
        name: f"{config['description']} [{config.get('status', 'unknown')}]"
        for name, config in DATASET_REGISTRY.items()
    }


def main():
    """CLI entry point for dataset download."""
    import argparse

    parser = argparse.ArgumentParser(description="Download evaluation datasets")
    parser.add_argument(
        "dataset",
        nargs="?",
        default="bbox-docvqa",
        help="Dataset to download (default: bbox-docvqa)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-download",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available datasets",
    )
    parser.add_argument(
        "--synthetic",
        type=int,
        default=None,
        metavar="N",
        help="Create synthetic dataset with N samples",
    )
    parser.add_argument(
        "--hf-token",
        type=str,
        default=None,
        help="Hugging Face token for gated datasets",
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

    if args.list:
        print("\nAvailable datasets:\n")
        for name, desc in list_available_datasets().items():
            print(f"  {name}: {desc}")
        print()
        return

    if args.synthetic:
        output_dir = args.output_dir or Path("data/synthetic")
        create_synthetic_dataset(output_dir, n_samples=args.synthetic)
        return

    output_dir = download_dataset(
        dataset_name=args.dataset,
        output_dir=args.output_dir,
        force=args.force,
        hf_token=args.hf_token,
    )

    print(f"\nDataset ready at: {output_dir}")
    print("\nTo run evaluation:")
    print(f"  python -m eval.benchmark --dataset {output_dir}")


if __name__ == "__main__":
    main()
