"""
Dataset loader for BBox_DocVQA_Bench benchmark dataset.

Dataset structure (JSONL):
- query/question: Natural-language prompt
- answer: Evidence-grounded response
- doc_name: ArXiv identifier
- evidence_page: List of 1-based page numbers
- image_paths/images: Relative paths to rendered pages
- bbox: Pixel coordinates [x_min, y_min, x_max, y_max]
- subimg_tpye: Box classification (text/table/image)
- category: ArXiv subject folder
"""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

from PIL import Image

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkSample:
    """A single benchmark sample with question, answer, and ground truth bounding boxes."""

    sample_id: int
    query: str
    answer: str
    doc_name: str
    category: str
    evidence_pages: List[int]
    image_paths: List[str]
    ground_truth_bboxes: List[List[List[int]]]  # Per page: list of [x1, y1, x2, y2]
    subimg_types: List[List[str]]  # Per page: list of types (text/table/image)
    raw_data: Dict[str, Any] = field(default_factory=dict)

    @property
    def num_pages(self) -> int:
        return len(self.image_paths)

    def get_image(self, page_idx: int, dataset_dir: Path) -> Optional[Image.Image]:
        """Load the image for a specific page."""
        if page_idx >= len(self.image_paths):
            return None

        image_path = dataset_dir / self.image_paths[page_idx]
        if not image_path.exists():
            logger.warning(f"Image not found: {image_path}")
            return None

        return Image.open(image_path)

    def get_all_images(self, dataset_dir: Path) -> List[Optional[Image.Image]]:
        """Load all images for this sample."""
        return [self.get_image(i, dataset_dir) for i in range(self.num_pages)]


class BBoxDocVQADataset:
    """
    Dataset loader for BBox_DocVQA_Bench.

    This dataset contains document VQA samples with ground truth bounding boxes
    indicating which regions contain the answer evidence.
    """

    def __init__(self, data_dir: str, jsonl_filename: str = "BBox_DocVQA_Bench.jsonl"):
        """
        Initialize the dataset loader.

        Args:
            data_dir: Path to the dataset directory containing images and JSONL file
            jsonl_filename: Name of the JSONL file containing annotations
        """
        self.data_dir = Path(data_dir)
        self.jsonl_path = self.data_dir / jsonl_filename
        self.samples: List[BenchmarkSample] = []
        self._loaded = False

    def load(self) -> "BBoxDocVQADataset":
        """Load the dataset from disk."""
        if self._loaded:
            return self

        if not self.jsonl_path.exists():
            raise FileNotFoundError(f"Dataset file not found: {self.jsonl_path}")

        logger.info(f"Loading dataset from {self.jsonl_path}")
        self.samples = []

        with open(self.jsonl_path, "r", encoding="utf-8") as f:
            for idx, line in enumerate(f):
                if not line.strip():
                    continue

                try:
                    data = json.loads(line)
                    sample = self._parse_sample(idx, data)
                    if sample:
                        self.samples.append(sample)
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse line {idx}: {e}")
                except Exception as e:
                    logger.warning(f"Error processing sample {idx}: {e}")

        self._loaded = True
        logger.info(f"Loaded {len(self.samples)} samples from dataset")
        return self

    def _parse_sample(self, idx: int, data: Dict[str, Any]) -> Optional[BenchmarkSample]:
        """Parse a single JSONL record into a BenchmarkSample."""
        # Handle both 'query' and 'question' field names
        query = data.get("query") or data.get("question", "")
        if not query:
            logger.warning(f"Sample {idx} missing query/question field")
            return None

        answer = data.get("answer", "")
        doc_name = data.get("doc_name", "")
        category = data.get("category", "")

        # Handle both 'evidence_page' (list) and 'evidence_pages' field names
        evidence_pages = data.get("evidence_page") or data.get("evidence_pages", [])
        if isinstance(evidence_pages, int):
            evidence_pages = [evidence_pages]

        # Handle both 'image_paths' and 'images' field names
        image_paths = data.get("image_paths") or data.get("images", [])
        if isinstance(image_paths, str):
            image_paths = [image_paths]

        # Parse bounding boxes - format is list of list of [x1, y1, x2, y2]
        # Structure: [[page1_bboxes], [page2_bboxes], ...]
        # Each page_bboxes: [[x1, y1, x2, y2], [x1, y1, x2, y2], ...]
        raw_bboxes = data.get("bbox", [])
        ground_truth_bboxes = self._normalize_bboxes(raw_bboxes)

        # Parse subimage types
        raw_types = data.get("subimg_tpye") or data.get("subimg_type", [])
        subimg_types = self._normalize_types(raw_types)

        return BenchmarkSample(
            sample_id=idx,
            query=query,
            answer=answer,
            doc_name=doc_name,
            category=category,
            evidence_pages=evidence_pages,
            image_paths=image_paths,
            ground_truth_bboxes=ground_truth_bboxes,
            subimg_types=subimg_types,
            raw_data=data,
        )

    def _normalize_bboxes(self, raw_bboxes: Any) -> List[List[List[int]]]:
        """Normalize bounding boxes to consistent format."""
        if not raw_bboxes:
            return []

        # If it's a flat list of coordinates, wrap it
        if raw_bboxes and isinstance(raw_bboxes[0], (int, float)):
            return [[[int(x) for x in raw_bboxes]]]

        # If it's a list of coordinates (one page)
        if raw_bboxes and isinstance(raw_bboxes[0], list):
            if raw_bboxes[0] and isinstance(raw_bboxes[0][0], (int, float)):
                return [[[int(x) for x in bbox] for bbox in raw_bboxes]]

            # It's already in the correct format (list of pages, each with list of bboxes)
            result = []
            for page_bboxes in raw_bboxes:
                if not page_bboxes:
                    result.append([])
                elif isinstance(page_bboxes[0], (int, float)):
                    # Single bbox for this page
                    result.append([[int(x) for x in page_bboxes]])
                else:
                    # Multiple bboxes for this page
                    result.append([[int(x) for x in bbox] for bbox in page_bboxes])
            return result

        return []

    def _normalize_types(self, raw_types: Any) -> List[List[str]]:
        """Normalize subimage types to consistent format."""
        if not raw_types:
            return []

        if isinstance(raw_types, str):
            return [[raw_types]]

        if isinstance(raw_types[0], str):
            return [raw_types]

        return raw_types

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> BenchmarkSample:
        if not self._loaded:
            self.load()
        return self.samples[idx]

    def __iter__(self) -> Iterator[BenchmarkSample]:
        if not self._loaded:
            self.load()
        return iter(self.samples)

    def get_by_category(self, category: str) -> List[BenchmarkSample]:
        """Get all samples for a specific arXiv category."""
        if not self._loaded:
            self.load()
        return [s for s in self.samples if s.category == category]

    def get_categories(self) -> List[str]:
        """Get all unique categories in the dataset."""
        if not self._loaded:
            self.load()
        return list(set(s.category for s in self.samples))

    def get_statistics(self) -> Dict[str, Any]:
        """Get dataset statistics."""
        if not self._loaded:
            self.load()

        total_bboxes = sum(
            sum(len(page_bboxes) for page_bboxes in sample.ground_truth_bboxes)
            for sample in self.samples
        )

        type_counts = {"text": 0, "table": 0, "image": 0}
        for sample in self.samples:
            for page_types in sample.subimg_types:
                for t in page_types:
                    if t in type_counts:
                        type_counts[t] += 1

        return {
            "total_samples": len(self.samples),
            "total_bboxes": total_bboxes,
            "categories": self.get_categories(),
            "type_distribution": type_counts,
            "avg_bboxes_per_sample": total_bboxes / len(self.samples) if self.samples else 0,
        }


def download_dataset(cache_dir: str, dataset_name: str = "Yuwh07/BBox_DocVQA_Bench") -> Path:
    """
    Download the BBox_DocVQA_Bench dataset from HuggingFace.

    Args:
        cache_dir: Directory to cache the dataset
        dataset_name: HuggingFace dataset identifier

    Returns:
        Path to the downloaded dataset directory
    """
    try:
        from huggingface_hub import snapshot_download
    except ImportError:
        raise ImportError(
            "huggingface_hub is required to download the dataset. "
            "Install it with: pip install huggingface_hub"
        )

    cache_path = Path(cache_dir)
    cache_path.mkdir(parents=True, exist_ok=True)

    logger.info(f"Downloading dataset {dataset_name} to {cache_path}")

    # Download the dataset
    dataset_path = snapshot_download(
        repo_id=dataset_name,
        repo_type="dataset",
        local_dir=cache_path / "BBox_DocVQA_Bench",
        local_dir_use_symlinks=False,
    )

    return Path(dataset_path)
