"""
Data loader for BBox-DocVQA benchmark dataset.

Handles loading the JSONL dataset and associated images from the HuggingFace cache.
"""

import json
import logging
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator, List, Optional, Tuple

from PIL import Image

logger = logging.getLogger(__name__)


@dataclass
class BBoxDocVQASample:
    """A single sample from the BBox-DocVQA dataset."""

    query: str
    answer: str
    doc_name: str
    category: str
    evidence_pages: List[int]
    image_paths: List[str]
    bboxes: List[List[List[int]]]  # Per-page list of bboxes, each bbox is [x1, y1, x2, y2]
    subimg_types: List[List[str]]  # Per-page list of types (text, table, image)

    @property
    def instance_type(self) -> str:
        """Classify sample as SPSBB, SPMBB, or MPMBB."""
        num_pages = len(self.image_paths)
        total_bboxes = sum(len(page_bboxes) for page_bboxes in self.bboxes)

        if num_pages == 1 and total_bboxes == 1:
            return "SPSBB"  # Single-Page Single-BBox
        elif num_pages == 1 and total_bboxes > 1:
            return "SPMBB"  # Single-Page Multi-BBox
        else:
            return "MPMBB"  # Multi-Page Multi-BBox

    @property
    def all_gt_bboxes(self) -> List[Tuple[int, List[int]]]:
        """Get all ground truth bboxes with their page indices."""
        result = []
        for page_idx, page_bboxes in enumerate(self.bboxes):
            for bbox in page_bboxes:
                result.append((page_idx, bbox))
        return result


class BBoxDocVQADataset:
    """
    Loader for the BBox-DocVQA benchmark dataset.

    Expected directory structure:
    dataset_path/
    ├── BBox_DocVQA_Bench.jsonl
    ├── BBox_DocVQA_Bench_Images.zip (optional, if images not extracted)
    └── <category>/<doc_name>/<doc_name>_<page>.png (after extraction)
    """

    def __init__(
        self,
        dataset_path: str,
        extract_images: bool = True,
        categories: Optional[List[str]] = None,
    ):
        """
        Initialize the dataset loader.

        Args:
            dataset_path: Path to the dataset directory
            extract_images: Whether to extract images from zip if needed
            categories: Filter to specific categories (None = all)
        """
        self.dataset_path = Path(dataset_path)
        self.categories = categories
        self.samples: List[BBoxDocVQASample] = []
        self._images_extracted = False

        # Validate dataset path
        self.jsonl_path = self.dataset_path / "BBox_DocVQA_Bench.jsonl"
        if not self.jsonl_path.exists():
            raise FileNotFoundError(f"Dataset file not found: {self.jsonl_path}")

        # Check for images
        self.images_zip = self.dataset_path / "BBox_DocVQA_Bench_Images.zip"
        if extract_images and self.images_zip.exists():
            self._extract_images_if_needed()

        # Load samples
        self._load_samples()

    def _extract_images_if_needed(self) -> None:
        """Extract images from zip if not already extracted."""
        # Check if first category folder exists
        test_dirs = ["cs", "econ", "eess", "math", "physics", "q-bio", "q-fin", "stat"]
        for test_dir in test_dirs:
            if (self.dataset_path / test_dir).exists():
                logger.debug("Images already extracted, skipping extraction")
                self._images_extracted = True
                return

        logger.info(f"Extracting images from {self.images_zip}")
        with zipfile.ZipFile(self.images_zip, "r") as zf:
            zf.extractall(self.dataset_path)
        self._images_extracted = True
        logger.info("Image extraction complete")

    def _load_samples(self) -> None:
        """Load all samples from the JSONL file."""
        logger.info(f"Loading samples from {self.jsonl_path}")
        with open(self.jsonl_path, "r", encoding="utf-8") as f:
            for line in f:
                data = json.loads(line.strip())
                sample = self._parse_sample(data)

                # Filter by category if specified
                if self.categories and sample.category not in self.categories:
                    continue

                self.samples.append(sample)

        logger.info(f"Loaded {len(self.samples)} samples")
        self._log_statistics()

    def _parse_sample(self, data: dict) -> BBoxDocVQASample:
        """Parse a JSON record into a BBoxDocVQASample."""
        return BBoxDocVQASample(
            query=data.get("query") or data.get("question", ""),
            answer=data["answer"],
            doc_name=data["doc_name"],
            category=data["category"],
            evidence_pages=data["evidence_page"],
            image_paths=data.get("image_paths") or data.get("images", []),
            bboxes=data["bbox"],
            subimg_types=data.get("subimg_tpye", []),  # Note: typo in original dataset
        )

    def _log_statistics(self) -> None:
        """Log dataset statistics."""
        type_counts = {"SPSBB": 0, "SPMBB": 0, "MPMBB": 0}
        category_counts: dict = {}
        subimg_type_counts: dict = {}

        for sample in self.samples:
            type_counts[sample.instance_type] += 1
            category_counts[sample.category] = category_counts.get(sample.category, 0) + 1
            for page_types in sample.subimg_types:
                for t in page_types:
                    subimg_type_counts[t] = subimg_type_counts.get(t, 0) + 1

        logger.info(f"Instance types: {type_counts}")
        logger.info(f"Categories: {category_counts}")
        logger.info(f"Sub-image types: {subimg_type_counts}")

    def __len__(self) -> int:
        return len(self.samples)

    def __iter__(self) -> Iterator[BBoxDocVQASample]:
        return iter(self.samples)

    def __getitem__(self, idx: int) -> BBoxDocVQASample:
        return self.samples[idx]

    def get_image(self, sample: BBoxDocVQASample, page_idx: int = 0) -> Image.Image:
        """
        Load an image for a sample.

        Args:
            sample: The sample to load the image for
            page_idx: Index of the page image to load

        Returns:
            PIL Image object
        """
        image_path = self.dataset_path / sample.image_paths[page_idx]
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")
        return Image.open(image_path).convert("RGB")

    def get_all_images(self, sample: BBoxDocVQASample) -> List[Image.Image]:
        """Load all images for a sample."""
        return [self.get_image(sample, i) for i in range(len(sample.image_paths))]

    def get_image_dimensions(
        self, sample: BBoxDocVQASample, page_idx: int = 0
    ) -> Tuple[int, int]:
        """Get image dimensions without loading full image."""
        image_path = self.dataset_path / sample.image_paths[page_idx]
        with Image.open(image_path) as img:
            return img.size  # (width, height)

    def filter_by_type(self, instance_type: str) -> List[BBoxDocVQASample]:
        """Filter samples by instance type (SPSBB, SPMBB, MPMBB)."""
        return [s for s in self.samples if s.instance_type == instance_type]

    def filter_by_subimg_type(self, subimg_type: str) -> List[BBoxDocVQASample]:
        """Filter samples by sub-image type (text, table, image)."""
        return [
            s
            for s in self.samples
            if any(subimg_type in types for types in s.subimg_types)
        ]

    def get_statistics(self) -> dict:
        """Get comprehensive dataset statistics."""
        stats = {
            "total_samples": len(self.samples),
            "instance_types": {"SPSBB": 0, "SPMBB": 0, "MPMBB": 0},
            "categories": {},
            "subimg_types": {},
            "total_bboxes": 0,
            "total_pages": 0,
            "unique_documents": set(),
        }

        for sample in self.samples:
            stats["instance_types"][sample.instance_type] += 1
            stats["categories"][sample.category] = (
                stats["categories"].get(sample.category, 0) + 1
            )
            stats["unique_documents"].add(sample.doc_name)
            stats["total_pages"] += len(sample.image_paths)

            for page_types in sample.subimg_types:
                for t in page_types:
                    stats["subimg_types"][t] = stats["subimg_types"].get(t, 0) + 1

            for page_bboxes in sample.bboxes:
                stats["total_bboxes"] += len(page_bboxes)

        stats["unique_documents"] = len(stats["unique_documents"])
        return stats
